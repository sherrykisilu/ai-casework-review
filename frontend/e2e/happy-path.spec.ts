import { expect, test } from "@playwright/test";

test("reviewer completes an evidence-grounded analysis", async ({ page }) => {
  await page.route("**/api/v1/auth/register/", (route) =>
    route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ token: "e2e-token" }) })
  );
  await page.route("**/api/v1/cases/", (route) =>
    route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: "case-e2e",
        title: "Urgent privacy escalation",
        source_text: "A privacy breach is urgent.",
        status: "completed",
        progress: 100,
        result: {
          summary: "Evidence-backed compliance risk identified.",
          findings: [{
            category: "compliance",
            severity: "high",
            summary: "Potential compliance signal detected.",
            evidence: [{ quote: "A privacy breach is urgent.", rationale: "Matched privacy signal." }]
          }],
          recommended_actions: ["Verify the cited evidence."],
          limitations: ["Human review required."],
          confidence: 0.85
        },
        error_code: "",
        error_message: "",
        trace_id: "trace-e2e",
        deduplicated: false
      })
    })
  );

  await page.goto("/");
  await page.getByRole("button", { name: "Create demo account" }).click();
  await page.getByRole("button", { name: "Analyze case" }).click();
  await expect(page.getByText("Evidence-backed compliance risk identified.")).toBeVisible();
  await expect(page.getByText("A privacy breach is urgent.")).toBeVisible();
});
