import crypto from "node:crypto";
import type { SupabaseClient, User } from "@supabase/supabase-js";
import { fixtureSpec } from "@/lib/fixture";

export const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
export const ALLOWED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

export function isFixtureMode() {
  return process.env.PRODUCT_TWIN_FIXTURE_MODE === "true";
}

export function assertImage(file: File, required: boolean) {
  if (!file || file.size === 0) {
    if (required) throw new Error("A front product photo is required.");
    return;
  }
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) throw new Error("Use a PNG, JPEG, or WebP image.");
  if (file.size > MAX_UPLOAD_BYTES) throw new Error("Images must be 15 MB or smaller.");
}

export function safeExtension(file: File) {
  const byType: Record<string, string> = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
  };
  return byType[file.type] ?? "bin";
}

export function draftSpec(heightMm: number) {
  const scale = heightMm / fixtureSpec.dimensions.heightMm;
  return {
    ...fixtureSpec,
    dimensions: {
      ...fixtureSpec.dimensions,
      heightMm,
      bodyDiameterMm: Number((fixtureSpec.dimensions.bodyDiameterMm * scale).toFixed(2)),
      neckDiameterMm: Number((fixtureSpec.dimensions.neckDiameterMm * scale).toFixed(2)),
      capHeightMm: Number((fixtureSpec.dimensions.capHeightMm * scale).toFixed(2)),
    },
    provenance: {
      inferredFromAssetIds: [],
      analysisProvider: "manual" as const,
      confidence: null,
    },
  };
}

export async function requireUser(supabase: SupabaseClient): Promise<User> {
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) throw new Error("Authentication is required.");
  return data.user;
}

export function hmacHeaders(path: string, body: string) {
  const secret = process.env.PRODUCT_TWIN_INTERNAL_SECRET;
  if (!secret) throw new Error("Worker authentication is not configured.");
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const digest = crypto.createHash("sha256").update(body).digest("hex");
  const signature = crypto
    .createHmac("sha256", secret)
    .update(`POST\n${path}\n${timestamp}\n${digest}`)
    .digest("hex");
  return {
    "x-product-twin-timestamp": timestamp,
    "x-product-twin-signature": signature,
  };
}
