import path from "node:path";
import { expect, test } from "@playwright/test";

test("deterministic fixture happy path", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Create a product twin" }).click();
  await expect(page.getByRole("heading", { name: "Build the twin, then approve the evidence." })).toBeVisible();
  const upload = page.getByLabel("Front product photo");
  await expect(upload).toBeEnabled();
  await upload.setInputFiles(
    path.resolve("../../packages/test-fixtures/round-dropper/source-front.png"),
  );
  await page.getByRole("button", { name: "Analyze packaging" }).click();

  await expect(page.getByRole("heading", { name: "Correct the physical model" })).toBeVisible();
  await expect(page.getByText("Fallback recorded · no silent model substitution")).toBeVisible();
  await page.getByLabel(/Body diameter/).fill("44");
  await expect(page.getByLabel(/Body diameter/)).toHaveValue("44");
  await page.getByRole("button", { name: "Approve specification and render" }).click();

  await expect(page.getByText("Generated twin", { exact: true })).toBeVisible({ timeout: 10_000 });
  const viewer = page.getByLabel("Interactive GLB product twin viewer");
  await expect(viewer).toBeVisible();
  await expect(viewer.getByRole("status")).toHaveText("GLB model loaded.");
  const studioRenders = page.getByRole("region", { name: "Studio renders" });
  await expect(studioRenders).toBeVisible();
  await expect(studioRenders.getByRole("img")).toHaveCount(3);
  await expect(studioRenders.getByText("Front transparent PNG", { exact: true })).toBeVisible();
  await expect(studioRenders.getByText("Three-quarter transparent PNG", { exact: true })).toBeVisible();
  await expect(studioRenders.getByText("White-background ecommerce PNG", { exact: true })).toBeVisible();

  const outputs = page.getByText("Secure outputs", { exact: true }).locator("..");
  const glbRow = outputs.getByText("GLB model", { exact: true }).locator("..");
  const glbDownload = glbRow.getByRole("link", { name: "Download" });
  await expect(glbDownload).toHaveAttribute("href", "/fixture/product.glb");
  await expect(glbDownload).toHaveAttribute("download", "product.glb");
});
