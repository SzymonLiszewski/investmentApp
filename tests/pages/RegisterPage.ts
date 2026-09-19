import { Page, Locator, expect } from '@playwright/test';

export class RegisterPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly submitButton: Locator;
  readonly alert: Locator;
  readonly status: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByPlaceholder('username');
    this.passwordInput = page.getByPlaceholder('password', { exact: true });
    this.confirmPasswordInput = page.getByPlaceholder('confirm password');
    this.submitButton = page.getByRole('button', { name: 'Register' });
    this.alert = page.getByRole('alert');
    this.status = page.getByRole('status');
  }

  async goto() {
    await this.page.goto('/register');
  }

  async register(username: string, password: string, confirmPassword = password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.confirmPasswordInput.fill(confirmPassword);
    await this.submitButton.click();
  }

  async expectError(message?: RegExp | string) {
    if (message) {
      await expect(this.alert).toHaveText(message);
    } else {
      await expect(this.alert).toBeVisible();
    }
  }

  async expectSuccess(message?: RegExp | string) {
    if (message) {
      await expect(this.status).toHaveText(message);
    } else {
      await expect(this.status).toBeVisible();
    }
  }
}
