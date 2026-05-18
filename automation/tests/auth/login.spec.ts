/**
 * TC-AUTH-001 | Login — Authentication Tests
 * Traceability: REQ-001 → US-001 (Authentication) → TC-AUTH-001
 */
import { test, expect } from "@fixtures/base";

const VALID_EMAIL = process.env.TEST_USER_EMAIL || "admin@qagent.dev";
const VALID_PASSWORD = process.env.TEST_USER_PASSWORD || "Admin@1234";

test.describe("Authentication", () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // Clear auth for these tests

  test("TC-AUTH-001 | Valid credentials redirect to dashboard", async ({ loginPage }) => {
    await test.step("Navigate to login page", async () => {
      await loginPage.navigate();
    });

    await test.step("Submit valid credentials", async () => {
      await loginPage.login(VALID_EMAIL, VALID_PASSWORD);
    });

    await test.step("Assert redirect to dashboard", async () => {
      await loginPage.assertURL(/\/dashboard/);
    });
  });

  test("TC-AUTH-002 | Invalid credentials show error", async ({ loginPage }) => {
    await test.step("Submit invalid credentials", async () => {
      await loginPage.tryInvalidLogin("invalid@example.com", "wrongpassword");
    });

    await test.step("Assert error is displayed", async () => {
      await loginPage.assertLoginError();
    });
  });

  test("TC-AUTH-003 | Empty email is rejected", async ({ loginPage }) => {
    await test.step("Navigate to login page", async () => {
      await loginPage.navigate();
    });

    await test.step("Submit with empty email", async () => {
      await loginPage.assertEmailRequired();
    });
  });

  test("TC-AUTH-004 | SQL injection in email field", async ({ loginPage, page }) => {
    await loginPage.navigate();
    await page.locator('input[type="email"]').fill("' OR '1'='1");
    await page.locator('input[type="password"]').fill("anypassword");
    await page.locator('button:has-text("Sign In")').click();

    // Should NOT redirect to dashboard
    await expect(page).not.toHaveURL(/\/dashboard/);
  });

  test("TC-AUTH-005 | XSS in login field", async ({ loginPage, page }) => {
    await loginPage.navigate();
    await page.locator('input[type="email"]').fill('<script>alert("xss")</script>');
    await page.locator('input[type="password"]').fill("password");
    await page.locator('button:has-text("Sign In")').click();

    // No alert dialog should appear
    let alertFired = false;
    page.on("dialog", () => { alertFired = true; });
    await page.waitForTimeout(1000);
    expect(alertFired).toBe(false);
  });
});
