import path from "node:path";
import { expect, test } from "@playwright/test";

test("deterministic fixture happy path", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Create a product twin" }).click();
  await page.getByLabel("Front product photo").setInputFiles(
    path.resolve("../../packages/test-fixtures/round-dropper/source-front.png"),
  );
  await page.getByRole("button", { name: "Analyze packaging" }).click();

  await expect(page.getByText("Correct the physical model")).toBeVisible();
  await expect(page.getByText(/Fallback recorded/i)).toBeVisible();
  await page.getByLabel(/Body diameter/).fill("44");
  await page.getByRole("button", { name: "Approve specification and render" }).click();

  await expect(page.getByText("Generated twin")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByLabel("Interactive GLB product twin viewer")).toBeVisible();
  const studioRenders = page.getByRole("region", { name: "Studio renders" });
  await expect(studioRenders).toBeVisible();
  await expect(studioRenders.getByText("Front transparent PNG")).toBeVisible();
  await expect(studioRenders.getByText("Three-quarter transparent PNG")).toBeVisible();
  await expect(studioRenders.getByText("White-background ecommerce PNG")).toBeVisible();

  const glbRow = page.getByText("GLB model").locator("..");
  const glbDownload = glbRow.getByRole("link", { name: "Download" });
  await expect(glbDownload).toHaveAttribute("href", "/fixture/product.glb");
  await expect(glbDownload).toHaveAttribute("download", "product.glb");
});
