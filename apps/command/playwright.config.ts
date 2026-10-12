import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";
export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  workers: 1,
  use: {
    baseURL: process.env.DEVA_TEST_URL ?? "http://127.0.0.1:5173",
    viewport: { width: 1600, height: 1000 },
    launchOptions: {
      executablePath: process.env.DEVA_CHROMIUM_PATH ?? "/usr/bin/chromium",
      args: [
        "--no-sandbox",
        "--use-gl=angle",
        "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader",
      ],
    },
    screenshot: "only-on-failure",
  },
  webServer: process.env.DEVA_TEST_URL ? [] : [
    {
      command:
        ".venv/bin/python -m uvicorn deva.api:app --host 127.0.0.1 --port 8000",
      cwd: resolve("../.."),
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: true,
      timeout: 30000,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
  reporter: "list",
});
