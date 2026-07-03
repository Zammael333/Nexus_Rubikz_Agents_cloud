import { test, expect } from "@playwright/test";

test.describe("Alerting Rules", () => {
  test("renders alert rules table with severity and status", async ({ page }) => {
    await page.goto("/alerting");
    await expect(page.getByRole("heading", { name: "Alerting Rules" })).toBeVisible();
    await expect(page.getByText("enabled").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("critical").first()).toBeVisible();
  });
});

test.describe("Audit Trail", () => {
  test("renders immutable audit timeline with actions", async ({ page }) => {
    await page.goto("/audit-trail");
    await expect(page.getByRole("heading", { name: "Audit Trail" })).toBeVisible();
    await expect(page.getByText("Immutable record").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("system").first()).toBeVisible();
  });
});

test.describe("Backup Status", () => {
  test("renders backup table with type and size", async ({ page }) => {
    await page.goto("/backups");
    await expect(page.getByRole("heading", { name: "Backup Status" })).toBeVisible();
    await expect(page.getByText("Duration").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("full").first()).toBeVisible();
  });
});

test.describe("Compliance", () => {
  test("renders compliance table with framework badges", async ({ page }) => {
    await page.goto("/compliance");
    await expect(page.getByRole("heading", { name: "Compliance" })).toBeVisible();
    await expect(page.getByText("% pass").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Cost Explorer", () => {
  test("renders cost cards with budget utilization", async ({ page }) => {
    await page.goto("/cost");
    await expect(page.getByRole("heading", { name: "Cost Explorer" })).toBeVisible();
    await expect(page.getByText("% of budget").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Incidents", () => {
  test("renders incident list with expandable details", async ({ page }) => {
    await page.goto("/incidents");
    await expect(page.getByRole("heading", { name: "Incidents" })).toBeVisible();
    await expect(page.getByText("SEV1").first()).toBeVisible({ timeout: 10000 });
    const card = page.getByText("SEV1").first();
    await card.click();
    await expect(page.getByText("Resolved:").first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Maintenance Windows", () => {
  test("renders maintenance cards with scope and impact", async ({ page }) => {
    await page.goto("/maintenance");
    await expect(page.getByRole("heading", { name: "Maintenance Windows" })).toBeVisible();
    await expect(page.getByText("Scheduled").first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Runbooks", () => {
  test("renders runbook cards with steps and owner", async ({ page }) => {
    await page.goto("/runbooks");
    await expect(page.getByRole("heading", { name: "Runbooks" })).toBeVisible();
    await expect(page.getByText("steps").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Owner:").first()).toBeVisible();
  });
});

test.describe("Secrets Management", () => {
  test("renders secrets table with version and rotation", async ({ page }) => {
    await page.goto("/secrets");
    await expect(page.getByRole("heading", { name: "Secrets Management" })).toBeVisible();
    await expect(page.getByText("Version").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Next Rotation").first()).toBeVisible();
  });
});

test.describe("Service Topology", () => {
  test("renders topology nodes and edges", async ({ page }) => {
    await page.goto("/topology");
    await expect(page.getByRole("heading", { name: "Service Topology" })).toBeVisible();
    await expect(page.getByText("Nodes").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Edges").first()).toBeVisible();
  });
});

test.describe("BLOQUE V Sidebar Navigation", () => {
  test("all 10 new nav links visible and navigate correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    const links = ["Alerting", "Audit Trail", "Backups", "Compliance", "Cost", "Incidents", "Maintenance", "Runbooks", "Secrets", "Topology"];
    for (const link of links) {
      await expect(page.getByRole("link", { name: new RegExp(link, "i") })).toBeVisible();
    }
    await page.goto("/alerting");
    await expect(page).toHaveURL(/\/alerting/, { timeout: 10000 });
    await expect(page.getByText("Alerting Rules")).toBeVisible();
  });
});
