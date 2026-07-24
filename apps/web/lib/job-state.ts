export const jobStatuses = ["queued", "rendering", "complete", "failed"] as const;
export type JobStatus = (typeof jobStatuses)[number];

const allowedTransitions: Record<JobStatus, readonly JobStatus[]> = {
  queued: ["rendering", "failed"],
  rendering: ["complete", "failed", "queued"],
  complete: [],
  failed: ["queued"],
};

export function canTransitionJob(from: JobStatus, to: JobStatus): boolean {
  return allowedTransitions[from].includes(to);
}

export function assertJobTransition(from: JobStatus, to: JobStatus): void {
  if (!canTransitionJob(from, to)) {
    throw new Error(`Invalid render job transition: ${from} -> ${to}`);
  }
}
