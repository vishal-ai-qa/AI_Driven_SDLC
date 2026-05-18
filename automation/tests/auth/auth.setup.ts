/**
 * Auth setup — runs once before all spec files.
 * Saves storage state (cookies + localStorage) to avoid re-logging in every spec.
 */
import { test as setup } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, "../../playwright/.auth/user.json");

setup("authenticate", async ({ page }) => {
  const baseUrl = process.env.BASE_URL || "http://localhost:3000";
  const email = process.env.TEST_USER_EMAIL || "admin@qagent.dev";
  const password = process.env.TEST_USER_PASSWORD || "Admin@1234";

  await page.goto(`${baseUrl}/login`);
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button:has-text("Sign In")').click();
  await page.waitForURL("**/dashboard", { timeout: 15_000 });

  await page.context().storageState({ path: authFile });
});
