import { NextResponse } from "next/server";
import { hmacHeaders, isFixtureMode, requireUser, workerStartUrl } from "@/lib/project-server";
import { createClient } from "@/lib/supabase/server";

const fixtureOutputs = [
  { kind: "render_front", filename: "front.png", url: "/fixture/front.png", mimeType: "image/png" },
  { kind: "render_three_quarter", filename: "three-quarter.png", url: "/fixture/three-quarter.png", mimeType: "image/png" },
  { kind: "render_ecommerce", filename: "ecommerce.png", url: "/fixture/ecommerce.png", mimeType: "image/png" },
  { kind: "model_glb", filename: "product.glb", url: "/fixture/product.glb", mimeType: "model/gltf-binary" },
  { kind: "debug_manifest", filename: "manifest.json", url: "/fixture/manifest.json", mimeType: "application/json" },
] as const;

export const dynamic = "force-dynamic";

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    if (isFixtureMode()) {
      return NextResponse.json({
        jobId: "00000000-0000-4000-8000-000000000002",
        status: "complete",
        currentStep: "saving outputs",
        outputs: fixtureOutputs,
      });
    }

    const supabase = await createClient();
    const user = await requireUser(supabase);
    const { data: approvedSpec, error: specError } = await supabase
      .from("packaging_specs")
      .select("id")
      .eq("project_id", id)
      .eq("is_approved", true)
      .order("version", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (specError) {
      return NextResponse.json({ error: "The approved specification could not be loaded." }, { status: 500 });
    }
    if (!approvedSpec) {
      return NextResponse.json(
        { error: "Approve the packaging specification before rendering." },
        { status: 409 },
      );
    }

    const { data: job, error: jobError } = await supabase
      .from("render_jobs")
      .insert({ project_id: id, user_id: user.id, status: "queued", current_step: "validating specification" })
      .select("id, status, current_step")
      .single();
    if (jobError) {
      return NextResponse.json({ error: "The render job could not be created." }, { status: 500 });
    }
    await supabase.from("projects").update({ status: "queued" }).eq("id", id);

    if (!process.env.PRODUCT_TWIN_WORKER_URL) {
      const message = "The render worker is not configured. Your approved specification is saved; rendering did not start.";
      await Promise.all([
        supabase
          .from("render_jobs")
          .update({
            status: "failed",
            current_step: "failed",
            error_code: "worker_unavailable",
            error_message: message,
            completed_at: new Date().toISOString(),
          })
          .eq("id", job.id),
        supabase.from("projects").update({ status: "failed" }).eq("id", id),
      ]);
      return NextResponse.json(
        { error: message, jobId: job.id, status: "failed", currentStep: "failed" },
        { status: 503 },
      );
    }

    const path = `/internal/jobs/${job.id}/start`;
    let response: Response;
    try {
      response = await fetch(workerStartUrl(path), {
        method: "POST",
        headers: hmacHeaders(path, ""),
        cache: "no-store",
      });
    } catch {
      const message = "The render worker could not be reached. The approved specification remains saved.";
      await Promise.all([
        supabase
          .from("render_jobs")
          .update({
            status: "failed",
            current_step: "failed",
            error_code: "worker_start_failed",
            error_message: message,
            completed_at: new Date().toISOString(),
          })
          .eq("id", job.id),
        supabase.from("projects").update({ status: "failed" }).eq("id", id),
      ]);
      return NextResponse.json(
        { error: message, jobId: job.id, status: "failed", currentStep: "failed" },
        { status: 503 },
      );
    }
    if (!response.ok) {
      const message = "The render worker rejected the job. The approved specification remains saved.";
      await Promise.all([
        supabase
          .from("render_jobs")
          .update({
            status: "failed",
            current_step: "failed",
            error_code: "worker_start_failed",
            error_message: message,
            completed_at: new Date().toISOString(),
          })
          .eq("id", job.id),
        supabase.from("projects").update({ status: "failed" }).eq("id", id),
      ]);
      return NextResponse.json(
        { error: message, jobId: job.id, status: "failed", currentStep: "failed" },
        { status: 502 },
      );
    }
    return NextResponse.json(
      { jobId: job.id, status: "queued", currentStep: "validating specification" },
      { status: 202 },
    );
  } catch {
    return NextResponse.json({ error: "Rendering could not be started." }, { status: 500 });
  }
}
