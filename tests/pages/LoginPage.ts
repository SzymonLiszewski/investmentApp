import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly alert: Locator;
  readonly status: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByPlaceholder('username');
    this.passwordInput = page.getByPlaceholder('password');
    this.submitButton = page.getByRole('button', { name: 'Login' });
    this.alert = page.getByRole('alert');
    this.status = page.getByRole('status');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message?: RegExp | string) {
    if (message) {
      await expect(this.alert).toHaveText(message);
    } else {
      await expect(this.alert).toBeVisible();
    }
  }
}
