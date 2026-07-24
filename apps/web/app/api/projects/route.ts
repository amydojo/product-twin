import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import {
  assertImage,
  draftSpec,
  isFixtureMode,
  requireUser,
  safeExtension,
  safeFilename,
} from "@/lib/project-server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const front = form.get("front");
    const label = form.get("label");
    const heightMm = Number(form.get("heightMm"));
    const name = String(form.get("name") || "Untitled product").trim().slice(0, 120);
    if (!(front instanceof File)) {
      return NextResponse.json({ error: "A front product photo is required." }, { status: 400 });
    }
    try {
      await assertImage(front, true);
      if (label instanceof File && label.size > 0) await assertImage(label, false);
    } catch (error) {
      const message =
        error instanceof Error &&
        /^(A front product photo|Use a PNG|Images must be|The image contents)/.test(error.message)
          ? error.message
          : "The uploaded image is invalid.";
      return NextResponse.json(
        { error: message },
        { status: 400 },
      );
    }
    if (!Number.isFinite(heightMm) || heightMm <= 20 || heightMm > 400) {
      return NextResponse.json(
        { error: "Total product height must be between 20 and 400 mm." },
        { status: 400 },
      );
    }

    const spec = draftSpec(heightMm);
    if (isFixtureMode()) {
      return NextResponse.json({
        projectId: "00000000-0000-4000-8000-000000000001",
        spec: {
          ...spec,
          provenance: { ...spec.provenance, analysisProvider: "deterministic-fixture", confidence: 1 },
        },
        sourceUrl: "/fixture/source-front.png",
        isolatedUrl: "/fixture/front.png",
        fallbackUsed: true,
        analysisSummary:
          "Fixture analysis estimated a round dropper from the visible silhouette. Every physical value remains editable.",
      });
    }

    const supabase = await createClient();
    const user = await requireUser(supabase);
    const { data: project, error: projectError } = await supabase
      .from("projects")
      .insert({ user_id: user.id, name: name || "Untitled product", status: "uploaded" })
      .select("id")
      .single();
    if (projectError) throw projectError;

    const frontPath = `${user.id}/${project.id}/source-front.${safeExtension(front)}`;
    const { error: frontUploadError } = await supabase.storage
      .from("product-uploads")
      .upload(frontPath, front, { contentType: front.type, upsert: false });
    if (frontUploadError) throw frontUploadError;

    const isolatedPath = `${user.id}/${project.id}/isolated-product.${safeExtension(front)}`;
    const { error: isolatedUploadError } = await supabase.storage
      .from("product-outputs")
      .upload(isolatedPath, front, { contentType: front.type, upsert: false });
    if (isolatedUploadError) throw isolatedUploadError;

    const assetRows: Record<string, unknown>[] = [
      {
        project_id: project.id,
        user_id: user.id,
        kind: "source_front",
        bucket: "product-uploads",
        object_path: frontPath,
        mime_type: front.type,
        byte_size: front.size,
        metadata: { originalName: safeFilename(front.name) },
      },
      {
        project_id: project.id,
        user_id: user.id,
        kind: "isolated_product",
        bucket: "product-outputs",
        object_path: isolatedPath,
        mime_type: front.type,
        byte_size: front.size,
        metadata: {
          provider: "noop",
          fallbackUsed: true,
          reason: "Background-removal weights were unavailable during draft analysis.",
        },
      },
    ];

    if (label instanceof File && label.size > 0) {
      const labelPath = `${user.id}/${project.id}/label.${safeExtension(label)}`;
      const { error: labelUploadError } = await supabase.storage
        .from("product-uploads")
        .upload(labelPath, label, { contentType: label.type, upsert: false });
      if (labelUploadError) throw labelUploadError;
      assetRows.push({
        project_id: project.id,
        user_id: user.id,
        kind: "label_artwork",
        bucket: "product-uploads",
        object_path: labelPath,
        mime_type: label.type,
        byte_size: label.size,
        metadata: { originalName: safeFilename(label.name) },
      });
    }

    const { data: assets, error: assetError } = await supabase
      .from("assets")
      .insert(assetRows)
      .select("id, kind, object_path");
    if (assetError) throw assetError;
    const sourceAsset = assets.find((asset) => asset.kind === "source_front");
    const labelAsset = assets.find((asset) => asset.kind === "label_artwork");
    const sourceAssetIds = sourceAsset ? [sourceAsset.id] : [];
    const connectedSpec = {
      ...spec,
      label: labelAsset
        ? { ...spec.label, mode: "uploaded-artwork" as const, artworkAssetId: labelAsset.id }
        : { ...spec.label, mode: "none" as const, artworkAssetId: null },
      provenance: { ...spec.provenance, inferredFromAssetIds: sourceAssetIds },
    };

    const { error: specError } = await supabase.from("packaging_specs").insert({
      project_id: project.id,
      user_id: user.id,
      version: 1,
      schema_version: "1.0.0",
      spec: connectedSpec,
      is_approved: false,
    });
    if (specError) throw specError;
    await supabase.from("projects").update({ status: "awaiting_review" }).eq("id", project.id);
    const [{ data: sourceSigned, error: sourceSignedError }, { data: isolatedSigned, error: isolatedSignedError }] =
      await Promise.all([
        supabase.storage.from("product-uploads").createSignedUrl(frontPath, 3600),
        supabase.storage.from("product-outputs").createSignedUrl(isolatedPath, 3600),
      ]);
    if (sourceSignedError) throw sourceSignedError;
    if (isolatedSignedError) throw isolatedSignedError;

    return NextResponse.json({
      projectId: project.id,
      spec: connectedSpec,
      sourceUrl: sourceSigned.signedUrl,
      isolatedUrl: isolatedSigned.signedUrl,
      fallbackUsed: true,
      analysisSummary:
        "Background-removal weights were unavailable. The unchanged source is shown as an explicit no-op isolation fallback, and the physical draft is anchored by the supplied height.",
    });
  } catch {
    return NextResponse.json({ error: "Project creation failed." }, { status: 500 });
  }
}
