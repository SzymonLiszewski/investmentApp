import { APIRequestContext } from '@playwright/test';

export const VALID_PASSWORD = 'Str0ngPass!';

export function uniqueUsername(prefix = 'e2e_user') {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
}

/** Creates a user directly via the API, bypassing the registration UI. */
export async function createUser(
  request: APIRequestContext,
  username: string,
  password = VALID_PASSWORD
) {
  const response = await request.post('http://127.0.0.1:8000/api/user/register/', {
    data: { username, password },
  });
  if (!response.ok()) {
    throw new Error(`Failed to create user "${username}": ${response.status()} ${await response.text()}`);
  }
}
