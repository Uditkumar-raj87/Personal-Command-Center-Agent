import { expect, test } from "@playwright/test";

test("capture, plan, edit, approve, and review a task", async ({ page }) => {
  const title = `Playwright task ${Date.now()}`;
  await page.goto("/capture");
  await page.getByPlaceholder("Prepare Q4 project brief").fill(title);
  await page.getByRole("button", { name: "Add to inbox" }).click();
  await expect(page.getByText(title)).toBeVisible();

  await page.goto("/today");
  await page.getByText(title).first().click();
  await page.getByRole("button", { name: "Generate plan" }).click();
  await expect(page.getByText("EDITABLE PROPOSAL")).toBeVisible();
  await page.getByRole("button", { name: "Move block down" }).click();
  await page.getByRole("button", { name: "Save edits" }).click();
  await page.getByRole("button", { name: "Approve" }).click();
  await page.getByRole("button", { name: "Save end-of-day review" }).click();
  await expect(page.getByText("COMPLETED")).toBeVisible();
});
