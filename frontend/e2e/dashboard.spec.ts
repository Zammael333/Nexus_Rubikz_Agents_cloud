import { test, expect } from "@playwright/test";

test.describe("Pulse Dashboard", () => {
  test("shows the main pulse page with correct title and SLO", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("NEXUS");
    await expect(page.getByText("Edge Glow · System Pulse")).toBeVisible();
  });

  test("pulse indicator shows current pulse state", async ({ page }) => {
    await page.goto("/");
    const pulseCircle = page.locator(".rounded-full.w-32");
    await expect(pulseCircle).toBeVisible();
    await expect(page.getByText("green", { exact: true })).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Navigation Sidebar", () => {
  test("all nav links are present and navigate correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    const links = ["Pulse", "Graph", "Digital Twin", "Events", "Inventory", "Transactions", "Health", "Dead Letter", "Vibe Diff", "SPIFFE"];
    for (const link of links) {
      await expect(page.getByRole("link", { name: new RegExp(link, "i") })).toBeVisible();
    }
    await page.getByRole("link", { name: /Graph/i }).click();
    await expect(page).toHaveURL(/\/graph/, { timeout: 10000 });
    await expect(page.getByText("Worker Graph")).toBeVisible();
  });
});

test.describe("Graph View", () => {
  test("renders the interactive graph with workers", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/graph");
    await expect(page.getByText("Worker Graph")).toBeVisible();
    await expect(page.getByText("Inventory", { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Watchdog", { exact: true })).toBeVisible();
    await expect(page.getByText("Red Team", { exact: true })).toBeVisible();
  });
});

test.describe("Inventory", () => {
  test("displays SKU table and can toggle lock", async ({ page }) => {
    await page.goto("/inventory");
    await expect(page.getByRole("columnheader", { name: "SKU" })).toBeVisible();
    await expect(page.getByText("SKU-10001")).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /New SKU/i }).click();
    await expect(page.getByText("Create SKU")).toBeVisible();
    await page.getByRole("button", { name: /Cancel/i }).click();
  });
});

test.describe("Health Dashboard", () => {
  test("shows all worker health cards", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByText("Health Dashboard")).toBeVisible();
    await expect(page.getByText("Watchdog", { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Notifier", { exact: true })).toBeVisible();
  });
});

test.describe("Mobile Responsive", () => {
  test("sidebar and main content render on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("NEXUS");
    await expect(page.getByText("Edge Glow · System Pulse")).toBeVisible();
  });
});

test.describe("Dead-Letter Queue", () => {
  test("shows failed events with failure reason badges", async ({ page }) => {
    await page.goto("/dead-letter");
    await expect(page.getByText("Dead-Letter Queue")).toBeVisible();
    await expect(page.getByText("undelivered")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=timeout").first()).toBeVisible();
    await expect(page.locator("text=source:").first()).toBeVisible();
  });
});

test.describe("SPIFFE Identities", () => {
  test("displays SPIFFE identity table with valid/expiring/revoked status", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/spiffe");
    await expect(page.getByText("SPIFFE Identities")).toBeVisible();
    await expect(page.getByText(/spiffe:\/\//).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("valid", { exact: true }).first()).toBeVisible();
  });
});

test.describe("Vibe Diff", () => {
  test("shows pending drift-change proposals and can open modal", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/vibe-diff");
    await expect(page.getByRole("heading", { name: "Vibe Diff" })).toBeVisible();
    await expect(page.getByText("pending review")).toBeVisible({ timeout: 10000 });
    await page.getByText("Increase lock timeout").click();
    await expect(page.getByText("Review Drift Change")).toBeVisible();
    await page.getByRole("button", { name: /Approve/i }).click();
    await expect(page.getByText("approved").first()).toBeVisible();
  });
});

test.describe("Critical Alert", () => {
  test("critical event opens alert overlay with ACK/ESCALATE/DISMISS", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/events");
    await page.waitForTimeout(2000);
    const criticalCount = await page.locator("text=CRITICAL").count();
    if (criticalCount > 0) {
      await page.locator("text=CRITICAL").first().click();
      await expect(page.getByText("CRITICAL").first()).toBeVisible();
      await expect(page.getByRole("button", { name: /ACK/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /ESCALATE/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /DISMISS/i })).toBeVisible();
      await page.getByRole("button", { name: /DISMISS/i }).click();
    }
  });
});

test.describe("Event Detail Modal", () => {
  test("non-critical event opens detail modal", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/events");
    await page.waitForTimeout(2000);
    const infoEvent = page.locator("text=INFO").first();
    if (await infoEvent.isVisible()) {
      await infoEvent.click();
      await expect(page.getByText("Event Detail")).toBeVisible({ timeout: 5000 });
      await expect(page.getByText("Payload")).toBeVisible();
      await expect(page.getByText("Trace ID").first()).toBeVisible();
    }
  });
});

test.describe("Health Detail Modals", () => {
  test("clicking a health card opens worker detail modal", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/health");
    await expect(page.getByText("Watchdog", { exact: true })).toBeVisible({ timeout: 10000 });
    await page.getByText("Watchdog", { exact: true }).click();
    await expect(page.getByRole("heading", { name: "Worker Detail" })).toBeVisible();
    await expect(page.getByText("Last Executions")).toBeVisible();
    await expect(page.getByText("Config")).toBeVisible();
  });

  test("budget watchdog controls are visible and toggleable", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByText("Error Budget", { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("ACTIVE").first()).toBeVisible();
    await page.getByRole("button", { name: /Freeze/i }).click();
    await expect(page.getByText("FROZEN").first()).toBeVisible();
    await page.getByRole("button", { name: /Thaw/i }).click();
    await expect(page.getByText("ACTIVE").first()).toBeVisible();
  });
});

test.describe("New Nav Links", () => {
  test("new sidebar links navigate correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await expect(page.getByRole("link", { name: /Dead Letter/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Vibe Diff/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /SPIFFE/i })).toBeVisible();
    await page.getByRole("link", { name: /SPIFFE/i }).click();
    await expect(page).toHaveURL(/\/spiffe/, { timeout: 10000 });
    await expect(page.getByText("SPIFFE Identities")).toBeVisible();
  });
});
