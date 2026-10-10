import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 1,
  reporter: "line",
  use: { baseURL: "http://127.0.0.1:3000", trace: "on-first-retry" },
  webServer: [
    { command: "python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000", cwd: "../..", url: "http://127.0.0.1:8000/health", reuseExistingServer: true, env: { DATABASE_URL: "sqlite:///./playwright.db", LLM_PROVIDER: "deterministic" } },
    { command: "npm run dev -- --hostname 127.0.0.1 --port 3000", cwd: ".", url: "http://127.0.0.1:3000/capture", reuseExistingServer: true },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
