import { Page, Locator, expect } from '@playwright/test';

export type CurrencyCode = 'PLN' | 'USD' | 'EUR' | 'GBP' | 'CHF' | 'JPY' | 'CAD';

/** Columns of the Active positions table, in DOM order. */
const POSITION_COLUMNS = {
  asset: 0,
  symbol: 1,
  type: 2,
  quantity: 3,
  avgPrice: 4,
  totalCost: 5,
  currentValue: 6,
  profit: 7,
  returnPct: 8,
} as const;
export type PositionColumn = keyof typeof POSITION_COLUMNS;

export class PortfolioPage {
  readonly page: Page;

  // Toolbar
  readonly addAssetsLink: Locator;
  readonly importTransactionsLink: Locator;
  readonly connectedAccountsLink: Locator;
  readonly currencyButton: Locator;

  // Dashboard sections
  readonly valueHistorySection: Locator;
  readonly compositionSection: Locator;
  readonly assetClassSection: Locator;
  readonly indicatorsSection: Locator;
  readonly positionsSection: Locator;

  // Active positions
  readonly positionsTable: Locator;
  readonly positionsEmptyMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    const toolbar = page.locator('.portfolioToolbarLinks');
    this.addAssetsLink = toolbar.getByRole('link', { name: 'Add assets' });
    this.importTransactionsLink = toolbar.getByRole('link', { name: 'Import transactions' });
    this.connectedAccountsLink = toolbar.getByRole('link', { name: 'Connected accounts' });
    this.currencyButton = page.getByRole('button', { name: 'Select currency' });

    this.valueHistorySection = page.locator('#return');
    this.compositionSection = page.locator('#composition');
    this.assetClassSection = page.locator('#compositionByClass');
    this.indicatorsSection = page.locator('#indicators');
    this.positionsSection = page.locator('#activePositions');

    this.positionsTable = this.positionsSection.getByRole('table', { name: 'Active positions' });
    this.positionsEmptyMessage = this.positionsSection.getByText('No positions yet');
  }

  async goto() {
    await this.page.goto('/portfolio');
  }

  async clickAddAssets() {
    await this.addAssetsLink.click();
  }

  async clickImportTransactions() {
    await this.importTransactionsLink.click();
  }

  /** Waits until the positions request has settled (spinner gone). */
  async waitForPositionsLoaded() {
    await expect(this.positionsSection).toBeVisible();
    await expect(this.positionsSection.getByRole('progressbar')).toHaveCount(0);
  }

  async selectCurrency(code: CurrencyCode) {
    await this.currencyButton.click();
    await this.page.locator('.currency-option').filter({ hasText: code }).click();
    await expect(this.currencyButton).toContainText(code);
  }

  /** A row in the positions table for the given symbol (or asset name). */
  positionRow(symbolOrName: string): Locator {
    return this.positionsTable.getByRole('row').filter({ hasText: symbolOrName });
  }

  /** A single cell of a position's row, e.g. positionCell('AAPL', 'totalCost'). */
  positionCell(symbolOrName: string, column: PositionColumn): Locator {
    return this.positionRow(symbolOrName).getByRole('cell').nth(POSITION_COLUMNS[column]);
  }

  /**
   * Opens the dashboard displayed in `code`. Waits for the initial (default
   * currency) load to settle first, so a slow first response can't land after
   * the switch and overwrite the newly selected currency.
   */
  async gotoInCurrency(code: CurrencyCode) {
    await this.goto();
    await this.waitForPositionsLoaded();
    await this.selectCurrency(code);
  }

  async expectPosition(symbolOrName: string) {
    await this.waitForPositionsLoaded();
    await expect(this.positionRow(symbolOrName)).toBeVisible();
  }

  async expectNoPositions() {
    await this.waitForPositionsLoaded();
    await expect(this.positionsEmptyMessage).toBeVisible();
    await expect(this.positionsTable).toHaveCount(0);
  }
}
