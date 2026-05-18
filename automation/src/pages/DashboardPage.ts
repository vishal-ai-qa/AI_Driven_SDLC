/**
 * DashboardPage — Page Object for the QAgent main dashboard.
 */
import { Page } from "@playwright/test";
import { BasePage } from "./BasePage";

export class DashboardPage extends BasePage {
  readonly path = "/dashboard";

  private get requirementsLink() { return this.page.getByRole("link", { name: /requirements/i }); }
  private get storiesLink() { return this.page.getByRole("link", { name: /user stories/i }); }
  private get testCasesLink() { return this.page.getByRole("link", { name: /test cases/i }); }
  private get executionLink() { return this.page.getByRole("link", { name: /execution/i }); }
  private get bugsLink() { return this.page.getByRole("link", { name: /bugs/i }); }

  get pipeline() { return this.page.locator('[data-testid="pipeline"], .agent-pipeline'); }
  get agentStatusBar() { return this.page.locator('[data-testid="agent-status"], .agent-status'); }

  async navigateToRequirements() { await this.requirementsLink.click(); }
  async navigateToStories() { await this.storiesLink.click(); }
  async navigateToTestCases() { await this.testCasesLink.click(); }
  async navigateToExecution() { await this.executionLink.click(); }
  async navigateToBugs() { await this.bugsLink.click(); }
}
