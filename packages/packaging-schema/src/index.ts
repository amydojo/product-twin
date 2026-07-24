import { z } from "zod";
const color = z.string().regex(/^#[0-9A-Fa-f]{6}$/);
export const packagingSpecSchema = z.object({
  schemaVersion: z.literal("1.0.0"),
  archetype: z.literal("round-dropper"),
  dimensions: z.object({
    heightMm: z.number().gt(20).max(400),
    bodyDiameterMm: z.number().gt(5).max(200),
    neckDiameterMm: z.number().gt(3).max(80),
    capHeightMm: z.number().gt(5).max(120),
    wallThicknessMm: z.number().gt(0.2).max(8),
  }).superRefine((d, ctx) => {
    if (d.neckDiameterMm >= d.bodyDiameterMm) ctx.addIssue({code:"custom", path:["neckDiameterMm"], message:"Neck must be narrower than body"});
    if (d.wallThicknessMm * 2 >= d.bodyDiameterMm) ctx.addIssue({code:"custom", path:["wallThicknessMm"], message:"Wall thickness leaves no inner volume"});
    if (d.capHeightMm >= d.heightMm * 0.7) ctx.addIssue({code:"custom", path:["capHeightMm"], message:"Cap is implausibly tall"});
  }),
  body: z.object({
    shoulderStartRatio: z.number().min(0.45).max(0.95), shoulderCurvature: z.number().min(0).max(1),
    material: z.enum(["clear-glass","frosted-glass","glossy-plastic","matte-plastic"]),
    colorHex: color, roughness: z.number().min(0).max(1), transmission: z.number().min(0).max(1), ior: z.number().min(1).max(2.5),
  }),
  closure: z.object({type:z.literal("dropper"), material:z.enum(["glossy-plastic","matte-plastic","metal"]), colorHex:color, roughness:z.number().min(0).max(1)}),
  liquid: z.object({enabled:z.boolean(), fillPercent:z.number().min(0).max(100), colorHex:color, opacity:z.number().min(0).max(1)}),
  label: z.object({mode:z.enum(["uploaded-artwork","none"]), placement:z.literal("front-decal"), artworkAssetId:z.string().uuid().nullable(), widthRatio:z.number().gt(0).max(0.95), heightRatio:z.number().gt(0).max(0.8), verticalCenterRatio:z.number().min(0.15).max(0.85)}),
  render: z.object({preset:z.literal("clean-studio"), resolution:z.number().int().min(512).max(4096), transparentBackground:z.boolean()}),
  provenance: z.object({inferredFromAssetIds:z.array(z.string().uuid()), analysisProvider:z.enum(["manual","birefnet","deterministic-fixture","noop"]), confidence:z.number().min(0).max(1).nullable()}),
}).superRefine((spec, ctx) => {
  if (!spec.liquid.enabled && spec.liquid.fillPercent !== 0) ctx.addIssue({code:"custom", path:["liquid","fillPercent"], message:"Disabled liquid must have zero fill"});
});
export type PackagingSpec = z.infer<typeof packagingSpecSchema>;
export function parsePackagingSpec(value: unknown): PackagingSpec { return packagingSpecSchema.parse(value); }
