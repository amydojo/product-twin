import { afterEach, describe, expect, it, vi } from "vitest";
import { assertImage, draftSpec, hmacHeaders, requireUser, safeExtension } from "./project-server";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("upload boundaries", () => {
  it("accepts supported images and derives extensions from MIME type", () => {
    const file = new File([new Uint8Array([1, 2, 3])], "untrusted.exe", { type: "image/png" });
    expect(() => assertImage(file, true)).not.toThrow();
    expect(safeExtension(file)).toBe("png");
  });

  it("rejects unsupported types and oversized payloads", () => {
    expect(() => assertImage(new File(["x"], "x.svg", { type: "image/svg+xml" }), true)).toThrow(/PNG, JPEG, or WebP/);
    const large = new File([new Uint8Array(15 * 1024 * 1024 + 1)], "large.png", { type: "image/png" });
    expect(() => assertImage(large, true)).toThrow(/15 MB/);
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
    vi.stubEnv("PRODUCT_TWIN_INTERNAL_SECRET", "test-secret-that-is-not-returned");
    const headers = hmacHeaders("/internal/jobs/00000000-0000-4000-8000-000000000001/start", "");
    expect(headers["x-product-twin-signature"]).toMatch(/^[a-f0-9]{64}$/);
    expect(JSON.stringify(headers)).not.toContain("test-secret");
  });
});
