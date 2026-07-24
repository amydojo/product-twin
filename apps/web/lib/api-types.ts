import type { PackagingSpec } from "@product-twin/packaging-schema";

export type OutputKind =
  | "render_front"
  | "render_three_quarter"
  | "render_ecommerce"
  | "model_glb"
  | "debug_manifest";

export type OutputAsset = {
  kind: OutputKind;
  filename: string;
  url: string;
  mimeType: string;
};

export type ProjectDraftResponse = {
  projectId: string;
  spec: PackagingSpec;
  sourceUrl: string;
  isolatedUrl: string | null;
  fallbackUsed: boolean;
  analysisSummary: string;
};

export type RenderResponse = {
  jobId: string;
  status: "queued" | "rendering" | "complete" | "failed";
  currentStep: string;
  outputs?: OutputAsset[];
};
