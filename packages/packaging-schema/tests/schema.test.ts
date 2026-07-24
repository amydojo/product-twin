import { describe, expect, it } from "vitest";
import fixture from "../../test-fixtures/round-dropper/spec.json";
import { packagingSpecSchema } from "../src/index";
describe("packaging specification", () => {
  it("accepts the canonical fixture", () => expect(packagingSpecSchema.safeParse(fixture).success).toBe(true));
  it("rejects negative dimensions", () => expect(packagingSpecSchema.safeParse({...fixture, dimensions:{...fixture.dimensions,heightMm:-1}}).success).toBe(false));
  it("rejects impossible fill", () => expect(packagingSpecSchema.safeParse({...fixture,liquid:{...fixture.liquid,fillPercent:101}}).success).toBe(false));
  it("rejects invalid colors", () => expect(packagingSpecSchema.safeParse({...fixture,body:{...fixture.body,colorHex:"cream"}}).success).toBe(false));
});
