/**
 * Base fixture — extends Playwright test with shared page objects and helpers.
 * All specs import from here, never directly from @playwright/test.
 */
import { test as base, expect, Page, APIRequestContext } from "@playwright/test";
import { LoginPage } from "@pages/LoginPage";
import { DashboardPage } from "@pages/DashboardPage";

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    // Auth state already loaded from storage via playwright.config.ts
    // No re-login needed in most specs
    await use(page);
  },
});

export { expect };
