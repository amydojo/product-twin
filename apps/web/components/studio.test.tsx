import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Studio } from "./studio";

describe("Studio upload", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ fixture: true }) }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requires a front product photo and total height", () => {
    render(<Studio />);
    expect(screen.getByLabelText(/front product photo/i)).toBeRequired();
    expect(screen.getByLabelText(/total product height/i)).toBeRequired();
    expect(screen.getByLabelText(/clean label artwork/i)).not.toBeRequired();
  });

  it("explains the controlled reconstruction before upload", () => {
    render(<Studio />);
    expect(screen.getByText(/isolate the product or record the fallback/i)).toBeVisible();
    expect(screen.getByText(/render only after explicit approval/i)).toBeVisible();
  });
});
