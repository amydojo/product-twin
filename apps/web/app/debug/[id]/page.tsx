import { packagingSpecSchema } from "@product-twin/packaging-schema";
import { notFound } from "next/navigation";
import fixtureManifest from "@/public/fixture/manifest.json";
import { fixtureSpec } from "@/lib/fixture";
import { isFixtureMode, requireUser } from "@/lib/project-server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

const blenderCommand = [
  "blender",
  "--background",
  "--python",
  "apps/worker/product_twin/blender/generate.py",
  "--",
  "--spec",
  "/work/spec.json",
  "--output",
  "/work/output",
];

export default async function DebugPage({ params }: { params: Promise<{ id: string }> }) {
  if (process.env.NODE_ENV === "production" && process.env.ENABLE_DEBUG_VIEW !== "true") notFound();
  const { id } = await params;

  if (isFixtureMode()) {
    const validation = packagingSpecSchema.safeParse(fixtureSpec);
    return <DebugEvidence id={id} evidence={{
      packagingSpec: fixtureSpec,
      validation: validation.success ? { valid: true } : { valid: false, issues: validation.error.issues },
      modelAnalysis: { provider: "deterministic-fixture", fallbackUsed: true },
      alphaMask: "/fixture/front.png",
      blenderCommand,
      generationManifest: fixtureManifest,
      workerLogs: "Structured logs are emitted by the worker and are not persisted in fixture mode.",
      outputMetadata: fixtureManifest.fileSizes,
    }} />;
  }

  const supabase = await createClient();
  await requireUser(supabase);
  const [{ data: specRow }, { data: assets }, { data: jobs }] = await Promise.all([
    supabase.from("packaging_specs").select("spec, schema_version, version, is_approved, created_at").eq("project_id", id).order("version", { ascending: false }).limit(1).maybeSingle(),
    supabase.from("assets").select("kind, bucket, object_path, mime_type, byte_size, width, height, metadata, created_at").eq("project_id", id).order("created_at"),
    supabase.from("render_jobs").select("status, current_step, attempt_count, error_code, error_message, started_at, completed_at, updated_at").eq("project_id", id).order("created_at", { ascending: false }).limit(5),
  ]);
  if (!specRow) notFound();

  const validation = packagingSpecSchema.safeParse(specRow.spec);
  const alphaAsset = assets?.find((asset) => asset.kind === "alpha_mask");
  let alphaMask: string | null = null;
  if (alphaAsset) {
    const { data } = await supabase.storage.from(alphaAsset.bucket).createSignedUrl(alphaAsset.object_path, 300);
    alphaMask = data?.signedUrl ?? null;
  }
  const manifestAsset = assets?.find((asset) => asset.kind === "debug_manifest");
  let generationManifest: unknown = null;
  if (manifestAsset) {
    const { data } = await supabase.storage.from(manifestAsset.bucket).download(manifestAsset.object_path);
    if (data) {
      try {
        generationManifest = JSON.parse(await data.text());
      } catch {
        generationManifest = { error: "Manifest is not valid JSON." };
      }
    }
  }

  return <DebugEvidence id={id} evidence={{
    packagingSpec: specRow,
    validation: validation.success ? { valid: true } : { valid: false, issues: validation.error.issues },
    modelAnalysis: assets?.find((asset) => asset.kind === "isolated_product")?.metadata ?? null,
    alphaMask,
    blenderCommand,
    generationManifest,
    workerLogs: jobs ?? [],
    outputMetadata: assets ?? [],
  }} />;
}

function DebugEvidence({ id, evidence }: { id: string; evidence: Record<string, unknown> }) {
  return (
    <main className="studio-main">
      <p className="eyebrow">Development-only evidence</p>
      <h1 className="studio-title">Debug manifest / {id}</h1>
      <div className="panel">
        <pre className="mono">{JSON.stringify(evidence, null, 2)}</pre>
      </div>
    </main>
  );
}
