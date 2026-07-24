import { afterEach, describe, expect, it, vi } from "vitest";
import {
  assertImage,
  draftSpec,
  hmacHeaders,
  requireUser,
  safeExtension,
  safeFilename,
  workerStartUrl,
} from "./project-server";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("upload boundaries", () => {
  it("accepts supported image signatures and derives extensions from MIME type", async () => {
    const file = new File(
      [new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])],
      "untrusted.exe",
      { type: "image/png" },
    );
    await expect(assertImage(file, true)).resolves.toBeUndefined();
    expect(safeExtension(file)).toBe("png");
  });

  it("rejects unsupported types, spoofed content, and oversized payloads", async () => {
    await expect(assertImage(new File(["x"], "x.svg", { type: "image/svg+xml" }), true)).rejects.toThrow(/PNG, JPEG, or WebP/);
    await expect(assertImage(new File(["not a png"], "x.png", { type: "image/png" }), true)).rejects.toThrow(/do not match/);
    const large = new File([new Uint8Array(15 * 1024 * 1024 + 1)], "large.png", { type: "image/png" });
    await expect(assertImage(large, true)).rejects.toThrow(/15 MB/);
  });

  it("normalizes untrusted display filenames", () => {
    expect(safeFilename("../../quarter\u0000.png")).toBe("_quarter_.png");
  });

  it("scales the manual draft while preserving valid physical relationships", () => {
    const spec = draftSpec(180);
    expect(spec.dimensions.heightMm).toBe(180);
    expect(spec.dimensions.bodyDiameterMm).toBe(63);
    expect(spec.dimensions.neckDiameterMm).toBeLessThan(spec.dimensions.bodyDiameterMm);
  });
});

describe("authorization and worker authentication", () => {
  it("requires a server-confirmed user", async () => {
    const authorized = { auth: { getUser: vi.fn().mockResolvedValue({ data: { user: { id: "user-1" } }, error: null }) } };
    await expect(requireUser(authorized as never)).resolves.toMatchObject({ id: "user-1" });

    const denied = { auth: { getUser: vi.fn().mockResolvedValue({ data: { user: null }, error: new Error("bad token") }) } };
    await expect(requireUser(denied as never)).rejects.toThrow(/authentication is required/i);
  });

  it("signs worker requests without exposing the secret", () => {
    vi.stubEnv("PRODUCT_TWIN_INTERNAL_SECRET", "test-secret-that-is-not-returned-32-bytes");
    const headers = hmacHeaders("/internal/jobs/00000000-0000-4000-8000-000000000001/start", "");
    expect(headers["x-product-twin-signature"]).toMatch(/^[a-f0-9]{64}$/);
    expect(headers["x-product-twin-nonce"]).toMatch(/^[a-f0-9]{32}$/);
    expect(JSON.stringify(headers)).not.toContain("test-secret");
  });

  it("rejects short HMAC secrets and unsafe worker URLs", () => {
    vi.stubEnv("PRODUCT_TWIN_INTERNAL_SECRET", "short");
    expect(() => hmacHeaders("/internal/jobs/1/start", "")).toThrow(/not configured/i);
    vi.stubEnv("PRODUCT_TWIN_WORKER_URL", "http://169.254.169.254/latest");
    expect(() => workerStartUrl("/internal/jobs/1/start")).toThrow(/HTTPS/);
    vi.stubEnv("PRODUCT_TWIN_WORKER_URL", "http://127.0.0.1:7860");
    expect(workerStartUrl("/internal/jobs/1/start").href).toBe("http://127.0.0.1:7860/internal/jobs/1/start");
  });
});
