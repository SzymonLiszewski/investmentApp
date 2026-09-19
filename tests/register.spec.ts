import { test, expect } from '@playwright/test';
import { RegisterPage } from './pages/RegisterPage';
import { createUser, uniqueUsername, VALID_PASSWORD } from './utils';

test.describe('Registration', () => {
  test('registers a new account and redirects to login', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    const username = uniqueUsername();

    await registerPage.goto();
    await registerPage.register(username, VALID_PASSWORD);

    await registerPage.expectSuccess(/account created/i);
    await expect(page).toHaveURL(/\/login$/, { timeout: 5000 });
  });

  test('rejects a password that does not meet the strength rules', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    const username = uniqueUsername();

    await registerPage.goto();
    await registerPage.register(username, 'weak');

    await registerPage.expectError(/at least 8 characters/i);
    await expect(page).toHaveURL(/\/register$/);
  });

  test('rejects mismatched passwords', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    const username = uniqueUsername();

    await registerPage.goto();
    await registerPage.register(username, VALID_PASSWORD, `${VALID_PASSWORD}x`);

    await registerPage.expectError(/passwords do not match/i);
  });

  test('rejects a username that is already taken', async ({ page, request }) => {
    const registerPage = new RegisterPage(page);
    const username = uniqueUsername();
    await createUser(request, username);

    await registerPage.goto();
    await registerPage.register(username, VALID_PASSWORD);

    await registerPage.expectError();
  });
});
