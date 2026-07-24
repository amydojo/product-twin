import { packagingSpecSchema } from "@product-twin/packaging-schema";
import { NextResponse } from "next/server";
import { isFixtureMode, requireUser } from "@/lib/project-server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const result = packagingSpecSchema.safeParse(await request.json());
    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid packaging specification", issues: result.error.issues },
        { status: 422 },
      );
    }
    if (isFixtureMode()) return NextResponse.json({ approved: true, version: 2, spec: result.data });

    const supabase = await createClient();
    const user = await requireUser(supabase);
    const { data: latest, error: readError } = await supabase
      .from("packaging_specs")
      .select("version")
      .eq("project_id", id)
      .order("version", { ascending: false })
      .limit(1)
      .single();
    if (readError) throw readError;

    const nextVersion = latest.version + 1;
    const { error: clearError } = await supabase
      .from("packaging_specs")
      .update({ is_approved: false })
      .eq("project_id", id)
      .eq("is_approved", true);
    if (clearError) throw clearError;

    const { error: insertError } = await supabase.from("packaging_specs").insert({
      project_id: id,
      user_id: user.id,
      version: nextVersion,
      schema_version: result.data.schemaVersion,
      spec: result.data,
      is_approved: true,
    });
    if (insertError) throw insertError;

    return NextResponse.json({ approved: true, version: nextVersion, spec: result.data });
  } catch {
    return NextResponse.json({ error: "Specification approval failed." }, { status: 500 });
  }
}
