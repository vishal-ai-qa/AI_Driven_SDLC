/**
 * LoginPage — Page Object for the QAgent login screen.
 */
import { Page, expect } from "@playwright/test";
import { BasePage } from "./BasePage";

export class LoginPage extends BasePage {
  readonly path = "/login";

  private get emailInput() { return this.page.locator('input[type="email"]'); }
  private get passwordInput() { return this.page.locator('input[type="password"]'); }
  private get submitButton() { return this.page.locator('button[type="submit"], button:has-text("Sign In")'); }
  private get errorMessage() { return this.page.locator('[data-testid="login-error"], .text-destructive'); }

  async login(email: string, password: string): Promise<void> {
    await this.navigate();
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
    await this.page.waitForURL("**/dashboard", { timeout: 10_000 });
  }

  async tryInvalidLogin(email: string, password: string): Promise<void> {
    await this.navigate();
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async assertLoginError(): Promise<void> {
    await expect(this.errorMessage).toBeVisible({ timeout: 5_000 });
  }

  async assertEmailRequired(): Promise<void> {
    await this.passwordInput.fill("anypassword");
    await this.submitButton.click();
    await expect(this.emailInput).toBeFocused();
  }
}
