import crypto from "node:crypto";
import type { SupabaseClient, User } from "@supabase/supabase-js";
import { fixtureSpec } from "@/lib/fixture";

export const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
export const ALLOWED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

export function isFixtureMode() {
  return process.env.PRODUCT_TWIN_FIXTURE_MODE === "true";
}

export async function assertImage(file: File, required: boolean) {
  if (!file || file.size === 0) {
    if (required) throw new Error("A front product photo is required.");
    return;
  }
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) throw new Error("Use a PNG, JPEG, or WebP image.");
  if (file.size > MAX_UPLOAD_BYTES) throw new Error("Images must be 15 MB or smaller.");
  const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer());
  const isPng =
    bytes.length >= 8 &&
    [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a].every((value, index) => bytes[index] === value);
  const isJpeg = bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  const isWebp =
    bytes.length >= 12 &&
    String.fromCharCode(...bytes.slice(0, 4)) === "RIFF" &&
    String.fromCharCode(...bytes.slice(8, 12)) === "WEBP";
  const matchesType =
    (file.type === "image/png" && isPng) ||
    (file.type === "image/jpeg" && isJpeg) ||
    (file.type === "image/webp" && isWebp);
  if (!matchesType) throw new Error("The image contents do not match the declared file type.");
}

export function safeExtension(file: File) {
  const byType: Record<string, string> = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
  };
  return byType[file.type] ?? "bin";
}

export function safeFilename(filename: string) {
  const normalized = filename
    .normalize("NFKC")
    .replace(/\.{2,}/g, "_")
    .replace(/[^\p{L}\p{N}._ -]+/gu, "_")
    .replace(/_+/g, "_")
    .replace(/^\.+/, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 120);
  return normalized || "upload";
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
  if (!secret || secret.length < 32) throw new Error("Worker authentication is not configured.");
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomBytes(16).toString("hex");
  const digest = crypto.createHash("sha256").update(body).digest("hex");
  const signature = crypto
    .createHmac("sha256", secret)
    .update(`POST\n${path}\n${timestamp}\n${nonce}\n${digest}`)
    .digest("hex");
  return {
    "x-product-twin-nonce": nonce,
    "x-product-twin-timestamp": timestamp,
    "x-product-twin-signature": signature,
  };
}

export function workerStartUrl(path: string) {
  const configured = process.env.PRODUCT_TWIN_WORKER_URL;
  if (!configured) throw new Error("The render worker is not configured.");
  const worker = new URL(configured);
  const loopback = worker.hostname === "127.0.0.1" || worker.hostname === "localhost" || worker.hostname === "::1";
  if (worker.username || worker.password || (worker.protocol !== "https:" && !(worker.protocol === "http:" && loopback))) {
    throw new Error("The render worker URL must use HTTPS, except for a loopback development worker.");
  }
  return new URL(path, worker);
}
