import { test as base, expect } from '@playwright/test';
import { AddAssetPage } from './pages/AddAssetPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { AuthTokens, createUser, loginViaApi, uniqueUsername, VALID_PASSWORD } from './utils';

export interface TestUser {
  username: string;
  password: string;
  tokens: AuthTokens;
}

interface Fixtures {
  /** A brand-new user with no transactions. */
  user: TestUser;
  portfolioPage: PortfolioPage;
  addAssetPage: AddAssetPage;
}

/**
 * page is overridden so every test starts logged in as a fresh user.
 * Tokens are injected into localStorage (same keys as src/api/client.js)
 * instead of clicking through the login form.
 */
export const test = base.extend<Fixtures>({
  user: async ({ request }, use) => {
    const username = uniqueUsername('e2e_portfolio');
    await createUser(request, username);
    const tokens = await loginViaApi(request, username);
    await use({ username, password: VALID_PASSWORD, tokens });
  },

  page: async ({ page, user }, use) => {
    await page.addInitScript(({ access, refresh }) => {
      localStorage.setItem('access', access);
      localStorage.setItem('refresh', refresh);
    }, user.tokens);
    await use(page);
  },

  portfolioPage: async ({ page }, use) => {
    await use(new PortfolioPage(page));
  },

  addAssetPage: async ({ page }, use) => {
    await use(new AddAssetPage(page));
  },
});

export { expect };
