import type { CurrencyCode } from './pages/PortfolioPage';

/**
 * Expected market data when the backend runs with USE_MOCK_DATA_FETCHER=true
 * (settings_e2e). These mirror the deterministic generators in
 * backend/base/infrastructure/providers/mock_fetchers.py
 * (_mock_price_for_symbol / _mock_fx_rate).
 */
export const MOCK_PRICE_USD = {
  AAPL: 188.86,
  'BTC-USD': 119.17,
} as const;

/** Units of <currency> per 1 USD. */
export const MOCK_USD_RATE: Record<CurrencyCode, number> = {
  USD: 1,
  PLN: 2.4,
  EUR: 2.6,
  GBP: 0.7,
  CHF: 4.7,
  JPY: 3.3,
  CAD: 3.8,
};

/** Formats like the Active positions table: 1,234.50 USD. */
export function formatMoney(value: number, currency: string): string {
  const amount = value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${amount} ${currency}`;
}

/** Formats like the Active positions table: +12.34% / -5.00%. */
export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

export interface OpenPosition {
  quantity: number;
  /** Average purchase price per unit, in USD. */
  avgCostUsd: number;
  /** Mock market price per unit, in USD. */
  priceUsd: number;
}

/** Text the Active positions table should show for position when displayed in currency. */
export function expectedPositionTexts(position: OpenPosition, currency: CurrencyCode) {
  const rate = MOCK_USD_RATE[currency];
  const totalCost = position.avgCostUsd * position.quantity * rate;
  const currentValue = position.priceUsd * position.quantity * rate;
  const profit = currentValue - totalCost;

  return {
    quantity: String(position.quantity),
    avgPrice: formatMoney(position.avgCostUsd * rate, currency),
    totalCost: formatMoney(totalCost, currency),
    currentValue: formatMoney(currentValue, currency),
    profit: formatMoney(profit, currency),
    // Return is a ratio, so it must not change with the display currency.
    returnPct: formatPercent((profit / totalCost) * 100),
  };
}
