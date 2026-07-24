import { NextResponse } from "next/server";
import { isFixtureMode, requireUser } from "@/lib/project-server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (isFixtureMode()) {
    return NextResponse.json({
      projectId: id,
      outputs: [
        { kind: "render_front", filename: "front.png", url: "/fixture/front.png", mimeType: "image/png" },
        { kind: "render_three_quarter", filename: "three-quarter.png", url: "/fixture/three-quarter.png", mimeType: "image/png" },
        { kind: "render_ecommerce", filename: "ecommerce.png", url: "/fixture/ecommerce.png", mimeType: "image/png" },
        { kind: "model_glb", filename: "product.glb", url: "/fixture/product.glb", mimeType: "model/gltf-binary" },
        { kind: "debug_manifest", filename: "manifest.json", url: "/fixture/manifest.json", mimeType: "application/json" },
      ],
    });
  }
  try {
    const supabase = await createClient();
    await requireUser(supabase);
    const { data: assets, error } = await supabase
      .from("assets")
      .select("kind, bucket, object_path, mime_type")
      .eq("project_id", id)
      .in("kind", ["render_front", "render_three_quarter", "render_ecommerce", "model_glb", "debug_manifest"]);
    if (error) throw error;
    const outputs = await Promise.all(
      assets.map(async (asset) => {
        const { data, error: signError } = await supabase.storage
          .from(asset.bucket)
          .createSignedUrl(asset.object_path, 900, { download: asset.object_path.split("/").at(-1) });
        if (signError) throw signError;
        return {
          kind: asset.kind,
          filename: asset.object_path.split("/").at(-1) ?? asset.kind,
          url: data.signedUrl,
          mimeType: asset.mime_type,
        };
      }),
    );
    return NextResponse.json({ projectId: id, outputs });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Results lookup failed." }, { status: 404 });
  }
}
