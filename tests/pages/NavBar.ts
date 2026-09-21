import { Page, Locator, expect } from '@playwright/test';

/**
 * The "Log in"/"Log out" buttons exist twice in the HTML (desktop bar +
 * hidden mobile drawer), so we scope to '.header-actions' to only match
 * the visible one.
 */
export class NavBar {
  readonly page: Page;
  readonly root: Locator;
  readonly logOutButton: Locator;
  readonly logInLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.root = page.locator('.header-actions');
    this.logOutButton = this.root.getByRole('button', { name: 'Log out' });
    this.logInLink = this.root.getByRole('link', { name: 'Log in' });
  }

  async logOut() {
    await this.logOutButton.click();
  }

  async expectLoggedIn() {
    await expect(this.logOutButton).toBeVisible();
    await expect(this.logInLink).toHaveCount(0);
  }

  async expectLoggedOut() {
    await expect(this.logInLink).toBeVisible();
  }
}
