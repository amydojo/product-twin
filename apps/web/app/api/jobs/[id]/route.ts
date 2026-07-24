import { NextResponse } from "next/server";
import { isFixtureMode, requireUser } from "@/lib/project-server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (isFixtureMode()) {
    return NextResponse.json({ jobId: id, status: "complete", currentStep: "saving outputs" });
  }
  try {
    const supabase = await createClient();
    await requireUser(supabase);
    const { data, error } = await supabase
      .from("render_jobs")
      .select("id, project_id, status, current_step, error_code, error_message, updated_at")
      .eq("id", id)
      .single();
    if (error) throw error;
    return NextResponse.json({
      jobId: data.id,
      projectId: data.project_id,
      status: data.status,
      currentStep: data.current_step,
      errorCode: data.error_code,
      errorMessage: data.error_message,
      updatedAt: data.updated_at,
    });
  } catch {
    return NextResponse.json({ error: "Job status could not be loaded." }, { status: 404 });
  }
}
