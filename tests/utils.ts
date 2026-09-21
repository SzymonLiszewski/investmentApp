import { APIRequestContext } from '@playwright/test';

export const API_URL = 'http://127.0.0.1:8000';
export const VALID_PASSWORD = 'Str0ngPass!';

export interface AuthTokens {
  access: string;
  refresh: string;
}

export function uniqueUsername(prefix = 'e2e_user') {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
}

/** Creates a user directly via the API, bypassing the registration UI. */
export async function createUser(
  request: APIRequestContext,
  username: string,
  password = VALID_PASSWORD
) {
  const response = await request.post(`${API_URL}/api/user/register/`, {
    data: { username, password },
  });
  if (!response.ok()) {
    throw new Error(`Failed to create user "${username}": ${response.status()} ${await response.text()}`);
  }
}

/** Obtains JWT tokens directly via the API, bypassing the login UI. */
export async function loginViaApi(
  request: APIRequestContext,
  username: string,
  password = VALID_PASSWORD
): Promise<AuthTokens> {
  const response = await request.post(`${API_URL}/api/token/`, {
    data: { username, password },
  });
  if (!response.ok()) {
    throw new Error(`Failed to log in "${username}": ${response.status()} ${await response.text()}`);
  }
  return (await response.json()) as AuthTokens;
}

export interface ApiTransaction {
  symbol: string;
  name: string;
  assetType: 'stocks' | 'cryptocurrencies';
  quantity: number;
  /** Price per unit in the asset's native currency. */
  price: number;
  type?: 'B' | 'S';
  /** ISO date; defaults to today, like the "Add assets" form does. */
  date?: string;
}

/** Records a transaction directly via the API, bypassing the "Add assets" form. */
export async function addTransactionViaApi(
  request: APIRequestContext,
  { access }: AuthTokens,
  tx: ApiTransaction
) {
  const response = await request.post(`${API_URL}/api/portfolio/transactions/`, {
    headers: { Authorization: `Bearer ${access}` },
    data: {
      symbol: tx.symbol,
      name: tx.name,
      asset_type: tx.assetType,
      transactionType: tx.type ?? 'B',
      quantity: tx.quantity,
      price: tx.price,
      // Must be sent: the backend falls back to 2024-01-01 when the date is omitted.
      date: tx.date ?? new Date().toISOString().split('T')[0],
    },
  });
  if (!response.ok()) {
    throw new Error(`Failed to add ${tx.symbol} transaction: ${response.status()} ${await response.text()}`);
  }
}
