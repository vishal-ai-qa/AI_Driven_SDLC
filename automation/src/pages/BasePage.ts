/**
 * BasePage — shared methods for all Page Objects.
 */
import { Page, Locator, expect } from "@playwright/test";

export abstract class BasePage {
  protected readonly page: Page;
  abstract readonly path: string;

  constructor(page: Page) {
    this.page = page;
  }

  async navigate(params?: Record<string, string>): Promise<void> {
    const url = params
      ? `${this.path}?${new URLSearchParams(params).toString()}`
      : this.path;
    await this.page.goto(url);
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState("networkidle");
  }

  async getTitle(): Promise<string> {
    return this.page.title();
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
  }

  protected locator(selector: string): Locator {
    return this.page.locator(selector);
  }

  protected getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  protected getByRole(role: Parameters<Page["getByRole"]>[0], options?: Parameters<Page["getByRole"]>[1]): Locator {
    return this.page.getByRole(role, options);
  }

  async assertVisible(locator: Locator, message?: string): Promise<void> {
    await expect(locator, message).toBeVisible();
  }

  async assertText(locator: Locator, text: string): Promise<void> {
    await expect(locator).toContainText(text);
  }

  async assertURL(pattern: string | RegExp): Promise<void> {
    await expect(this.page).toHaveURL(pattern);
  }
}
