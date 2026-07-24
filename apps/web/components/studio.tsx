"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { packagingSpecSchema, type PackagingSpec } from "@product-twin/packaging-schema";
import type { OutputAsset, ProjectDraftResponse, RenderResponse } from "@/lib/api-types";
import { fixtureSpec } from "@/lib/fixture";
import { ApproxPreview } from "./approx-preview";
import { GlbViewer } from "./glb-viewer";
import { SpecEditor } from "./spec-editor";
import { StatusTimeline } from "./status-timeline";

type Phase = "upload" | "review" | "rendering" | "results";
type UploadFields = { front: FileList; label?: FileList; heightMm: number; name?: string };

const outputLabels: Record<OutputAsset["kind"], string> = {
  render_front: "Front transparent PNG",
  render_three_quarter: "Three-quarter transparent PNG",
  render_ecommerce: "White-background ecommerce PNG",
  model_glb: "GLB model",
  debug_manifest: "Debug manifest",
};

export function Studio() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [spec, setSpec] = useState<PackagingSpec>(fixtureSpec);
  const [project, setProject] = useState<ProjectDraftResponse | null>(null);
  const [outputs, setOutputs] = useState<OutputAsset[]>([]);
  const [currentStep, setCurrentStep] = useState("validating specification");
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<UploadFields>();
  const validation = useMemo(() => packagingSpecSchema.safeParse(spec), [spec]);

  useEffect(() => {
    fetch("/api/auth/anonymous", { method: "POST" }).catch(() => undefined);
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  const upload = handleSubmit(async (values) => {
    setError(null);
    const front = values.front?.[0];
    if (!front) return setError("Choose a front product photo.");
    const form = new FormData();
    form.set("front", front);
    const label = values.label?.[0];
    if (label) form.set("label", label);
    form.set("heightMm", String(values.heightMm));
    form.set("name", values.name ?? "");
    const response = await fetch("/api/projects", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) return setError(payload.error ?? "Project creation failed.");
    setProject(payload as ProjectDraftResponse);
    setSpec((payload as ProjectDraftResponse).spec);
    setPhase("review");
  });

  async function loadResults(projectId: string) {
    const response = await fetch(`/api/projects/${projectId}/results`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error ?? "Results could not be loaded.");
    setOutputs(payload.outputs as OutputAsset[]);
    setPhase("results");
  }

  async function pollJob(jobId: string, projectId: string) {
    const response = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error ?? "Job status could not be loaded.");
    setCurrentStep(job.currentStep);
    if (job.status === "complete") return loadResults(projectId);
    if (job.status === "failed") throw new Error(job.errorMessage ?? "Rendering failed.");
    pollRef.current = setTimeout(() => void pollJob(jobId, projectId).catch(handleAsyncError), 1200);
  }

  function handleAsyncError(cause: unknown) {
    setError(cause instanceof Error ? cause.message : "Something went wrong.");
    setPhase("review");
  }

  async function approveAndRender() {
    if (!project || !validation.success) return;
    setError(null);
    try {
      const approval = await fetch(`/api/projects/${project.projectId}/spec`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(validation.data),
      });
      const approvalBody = await approval.json();
      if (!approval.ok) throw new Error(approvalBody.error ?? "Specification approval failed.");
      setPhase("rendering");
      const response = await fetch(`/api/projects/${project.projectId}/render`, { method: "POST" });
      const render = (await response.json()) as RenderResponse & { error?: string };
      if (!response.ok) throw new Error(render.error ?? "Rendering could not start.");
      setCurrentStep(render.currentStep);
      if (render.status === "complete" && render.outputs) {
        setOutputs(render.outputs);
        setPhase("results");
      } else {
        await pollJob(render.jobId, project.projectId);
      }
    } catch (cause) {
      handleAsyncError(cause);
    }
  }

  const glb = outputs.find((asset) => asset.kind === "model_glb");
  const imageOutputs = outputs.filter((asset) => asset.kind.startsWith("render_"));

  return (
    <main className="studio-main">
      <p className="eyebrow">Controlled round-dropper reconstruction</p>
      <h1 className="studio-title">Build the twin, then approve the evidence.</h1>
      {error ? <div className="error" role="alert">{error}</div> : null}

      {phase === "upload" ? (
        <form className="grid" onSubmit={upload} noValidate>
          <div className="panel">
            <h2>1. Give it one clean front view.</h2>
            <p className="note">PNG, JPEG, or WebP. Maximum 15 MB. Total height anchors the physical scale.</p>
            <div className="field">
              <label htmlFor="front">Front product photo</label>
              <input
                id="front"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                required
                {...register("front", { required: true })}
              />
              {errors.front ? <span className="field-error">A front photo is required.</span> : null}
            </div>
            <div className="field field-gap">
              <label htmlFor="label">Clean label artwork (optional)</label>
              <input id="label" type="file" accept="image/png,image/jpeg,image/webp" {...register("label")} />
            </div>
            <div className="field field-gap">
              <label htmlFor="heightMm">Total product height (mm)</label>
              <input
                id="heightMm"
                type="number"
                defaultValue="120"
                min="21"
                max="400"
                step="0.1"
                required
                {...register("heightMm", { required: true, valueAsNumber: true, min: 21, max: 400 })}
              />
            </div>
            <div className="field field-gap">
              <label htmlFor="name">Product name (optional)</label>
              <input id="name" placeholder="Field Serum 01" maxLength={120} {...register("name")} />
            </div>
            <button className="button" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Preparing draft…" : "Analyze packaging"}
            </button>
          </div>
          <div className="panel method-panel">
            <p className="eyebrow">What happens next</p>
            <ol className="method-list">
              <li>Isolate the product or record the fallback.</li>
              <li>Estimate a round-dropper specification.</li>
              <li>Let you correct every important physical decision.</li>
              <li>Render only after explicit approval.</li>
            </ol>
          </div>
        </form>
      ) : null}

      {phase === "review" && project ? (
        <div className="grid">
          <div className="panel">
            <SpecEditor spec={spec} onChange={setSpec} />
            {!validation.success ? (
              <p role="alert" className="field-error">Fix the invalid physical values before rendering.</p>
            ) : null}
            <button disabled={!validation.success} className="button" onClick={approveAndRender} type="button">
              Approve specification and render
            </button>
          </div>
          <div>
            <div className="panel evidence-panel">
              <p className="eyebrow">Detection evidence</p>
              <div className="evidence-grid">
                <figure>
                  <img src={project.sourceUrl} alt="Original front product" />
                  <figcaption>Original</figcaption>
                </figure>
                <figure>
                  {project.isolatedUrl ? <img src={project.isolatedUrl} alt="Isolated product result" /> : <div className="empty-evidence">Pending worker analysis</div>}
                  <figcaption>Isolation</figcaption>
                </figure>
              </div>
              <p className="note">{project.analysisSummary}</p>
              {project.fallbackUsed ? <p className="fallback-note">Fallback recorded · no silent model substitution</p> : null}
            </div>
            <ApproxPreview spec={spec} />
          </div>
        </div>
      ) : null}

      {phase === "rendering" ? (
        <div className="grid">
          <div className="panel">
            <p className="eyebrow">Database-backed render job</p>
            <h2>Rendering from the approved specification.</h2>
            <p className="note">The current step comes from the worker job record. No percentage theater.</p>
            <StatusTimeline currentStep={currentStep} />
          </div>
          <ApproxPreview spec={spec} />
        </div>
      ) : null}

      {phase === "results" ? (
        <div>
          <div className="grid results-grid">
            <div className="panel">
              <p className="eyebrow">Generated twin</p>
              {glb ? <GlbViewer src={glb.url} /> : <p className="note">GLB output is unavailable.</p>}
              <p className="note">Drag to orbit. Scroll to zoom. The GLB is the reusable geometry output.</p>
            </div>
            <div className="panel">
              <p className="eyebrow">Secure outputs</p>
              {outputs.map((asset) => (
                <div className="stage" key={asset.kind}>
                  <span>{outputLabels[asset.kind]}</span>
                  <a className="button secondary" href={asset.url} download={asset.filename}>Download</a>
                </div>
              ))}
              <details>
                <summary>Approved packaging specification</summary>
                <pre className="mono">{JSON.stringify(spec, null, 2)}</pre>
              </details>
            </div>
          </div>
          <div className="render-gallery" role="region" aria-label="Studio renders">
            {imageOutputs.map((asset) => (
              <figure className="render-card panel" key={asset.kind}>
                <img src={asset.url} alt={outputLabels[asset.kind]} />
                <figcaption>{outputLabels[asset.kind]}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      ) : null}
    </main>
  );
}
