import { expect, test } from "@playwright/test";

const api = process.env.API_BASE_URL || "http://127.0.0.1:8000";

test("captures, plans, edits, approves, reviews, and audits a task", async ({ page, request }) => {
  const task = await request.post(`${api}/api/tasks`, { data: { title: "Prepare browser release notes", estimated_minutes: 30, energy_level: "medium", priority_tag: "important", source: "web_form" } });
  expect(task.ok()).toBeTruthy();
  const taskData = await task.json();

  await page.goto("/today");
  await page.getByText("Prepare browser release notes").click();
  await page.getByRole("button", { name: "Generate plan" }).click();
  await expect(page.getByText("Editable proposal")).toBeVisible();
  await expect(page.getByText("Deterministic baseline")).toBeVisible();

  const end = page.getByLabel("Prepare browser release notes end");
  await end.fill("2026-10-10T10:00");
  await page.getByRole("button", { name: "Save edits" }).click();
  await expect(page.getByText("LOCAL EDITS")).toBeVisible();
  await page.getByRole("button", { name: "Approve plan" }).click();
  await expect(page.getByText(/APPROVED/)).toBeVisible();

  await page.getByRole("button", { name: "Mark task complete" }).click();
  await expect(page.getByText("completed 1")).toBeVisible();

  const review = await request.post(`${api}/api/plans/${(await (await request.get(`${api}/api/plans`)).json())[0].id}/review`, { data: [{ task_id: taskData.id, completed: true, notes: "Verified in browser flow" }] });
  expect(review.ok()).toBeTruthy();
  await page.reload();
});
