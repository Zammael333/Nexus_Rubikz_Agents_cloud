import { test, expect } from "@playwright/test";

test.describe("SLO Dashboard", () => {
  test("renders SLO gauge and error budget info", async ({ page }) => {
    await page.goto("/slo");
    await expect(page.getByRole("heading", { name: "SLO Dashboard" })).toBeVisible();
    await expect(page.getByText("Budget Remaining").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("fails/month")).toBeVisible();
  });
});

test.describe("Twin Timeline", () => {
  test("renders kernel/twin diff timeline", async ({ page }) => {
    await page.goto("/twin-timeline");
    await expect(page.getByRole("heading", { name: "Twin Timeline" })).toBeVisible();
    await expect(page.getByText("MATCH").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Einstein-Williams Traces", () => {
  test("renders waterfall spans and expands trace", async ({ page }) => {
    await page.goto("/traces");
    await expect(page.getByRole("heading", { name: "Einstein-Williams Traces" })).toBeVisible();
    await expect(page.getByText("trace-").first()).toBeVisible({ timeout: 10000 });
    const expandBtn = page.getByRole("button").first();
    if (await expandBtn.isVisible()) {
      await expandBtn.click();
    }
  });
});

test.describe("Worker Heatmap", () => {
  test("renders heatmap grid with metric tabs", async ({ page }) => {
    await page.goto("/heatmap");
    await expect(page.getByRole("heading", { name: "Worker Heatmap" })).toBeVisible();
    await expect(page.getByText("memory").first()).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: "errors" }).click();
    await expect(page.getByRole("button", { name: "errors" })).toBeVisible();
  });
});

test.describe("Scorpion Scans", () => {
  test("renders scan history table", async ({ page }) => {
    await page.goto("/scans");
    await expect(page.getByRole("heading", { name: "Scorpion Scans" })).toBeVisible();
    await expect(page.getByText("Scan ID").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Dead Stock").first()).toBeVisible();
  });
});

test.describe("Trust Scores", () => {
  test("renders trust score chart with worker toggles", async ({ page }) => {
    await page.goto("/trust");
    await expect(page.getByRole("heading", { name: "Trust Scores" })).toBeVisible();
    await expect(page.getByText("All").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Error Budget History", () => {
  test("renders budget burn-down chart and KPI cards", async ({ page }) => {
    await page.goto("/budget");
    await expect(page.getByRole("heading", { name: "Error Budget History" })).toBeVisible();
    await expect(page.getByText("Budget Remaining").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Latest Consumption").first()).toBeVisible();
  });
});

test.describe("Phoenix Protocol History", () => {
  test("renders recovery timeline with RTO icons", async ({ page }) => {
    await page.goto("/phoenix-history");
    await expect(page.getByRole("heading", { name: "Phoenix Protocol History" })).toBeVisible();
    await expect(page.getByText("Total Recoveries").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Cloud Monitoring", () => {
  test("renders GCP metric cards and alerts", async ({ page }) => {
    await page.goto("/cloud-monitoring");
    await expect(page.getByRole("heading", { name: "Cloud Monitoring" })).toBeVisible();
    await expect(page.getByText("Compute Engine CPU").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("BLOQUE IV Sidebar Navigation", () => {
  test("all 9 new nav links visible and navigate correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    const links = ["SLO", "Twin Timeline", "Traces", "Heatmap", "Scans", "Trust", "Error Budget", "Phoenix History", "Cloud"];
    for (const link of links) {
      await expect(page.getByRole("link", { name: new RegExp(link, "i") })).toBeVisible();
    }
    await page.goto("/slo");
    await expect(page).toHaveURL(/\/slo/, { timeout: 10000 });
    await expect(page.getByText("SLO Dashboard")).toBeVisible();
  });
});
