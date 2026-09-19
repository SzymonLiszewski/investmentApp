import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { NavBar } from './pages/NavBar';
import { createUser, uniqueUsername, VALID_PASSWORD } from './utils';

test.describe('Login', () => {
  test('logs in with valid credentials and updates the nav', async ({ page, request }) => {
    const loginPage = new LoginPage(page);
    const navBar = new NavBar(page);
    const username = uniqueUsername();
    await createUser(request, username);

    await loginPage.goto();
    await loginPage.login(username, VALID_PASSWORD);

    await expect(page).toHaveURL('/');
    await navBar.expectLoggedIn();
  });

  test('shows an error for an unknown username', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(uniqueUsername('no_such_user'), VALID_PASSWORD);

    await loginPage.expectError();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('shows an error for the wrong password', async ({ page, request }) => {
    const loginPage = new LoginPage(page);
    const username = uniqueUsername();
    await createUser(request, username);

    await loginPage.goto();
    await loginPage.login(username, 'WrongPassword1');

    await loginPage.expectError();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('logging out returns the nav to its logged-out state', async ({ page, request }) => {
    const loginPage = new LoginPage(page);
    const navBar = new NavBar(page);
    const username = uniqueUsername();
    await createUser(request, username);

    await loginPage.goto();
    await loginPage.login(username, VALID_PASSWORD);
    await navBar.expectLoggedIn();

    await navBar.logOut();

    await navBar.expectLoggedOut();
  });
});
