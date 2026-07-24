import { describe, expect, it } from "vitest";
import { assertJobTransition, canTransitionJob } from "./job-state";

describe("render job state transitions", () => {
  it("allows the database-backed happy path", () => {
    expect(canTransitionJob("queued", "rendering")).toBe(true);
    expect(canTransitionJob("rendering", "complete")).toBe(true);
  });

  it("allows bounded recovery but rejects terminal rewrites", () => {
    expect(canTransitionJob("rendering", "queued")).toBe(true);
    expect(canTransitionJob("failed", "queued")).toBe(true);
    expect(() => assertJobTransition("complete", "rendering")).toThrow(/invalid render job transition/i);
  });
});
