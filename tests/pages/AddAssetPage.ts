import { Page, Locator, expect } from '@playwright/test';

export type AssetType = 'Stocks' | 'Bonds' | 'Cryptocurrencies';
export type TransactionType = 'Buy' | 'Sell';

export interface TransactionDetails {
  quantity: number | string;
  type?: TransactionType;
  /** Leave undefined to use the closing price for the date. */
  price?: number | string;
  /** ISO date, e.g. '2024-01-15'. Leave undefined for today. */
  date?: string;
}

/**
 * Page object for /addStock (the "Add Assets" form).
 * Changing the asset type resets the form, so call selectAssetType() first.
 */
export class AddAssetPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly submitButton: Locator;

  readonly assetTypeSelect: Locator;
  readonly transactionTypeSelect: Locator;

  readonly searchInput: Locator;
  readonly suggestions: Locator;
  readonly symbolInput: Locator;
  readonly nameInput: Locator;

  readonly quantityInput: Locator;
  readonly priceInput: Locator;
  readonly dateInput: Locator;

  // Bonds
  readonly bondModeSelect: Locator;
  readonly bondTypeSelect: Locator;
  readonly bondSeriesInput: Locator;
  readonly maturityDateInput: Locator;
  readonly interestRateTypeSelect: Locator;
  readonly interestRateInput: Locator;
  readonly wiborMarginInput: Locator;
  readonly baseInterestRateInput: Locator;
  readonly inflationMarginInput: Locator;
  readonly faceValueInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Add Assets' });
    this.submitButton = page.getByRole('button', { name: /^(Add Assets|Adding)/ });

    this.assetTypeSelect = this.select(/^Asset Type/);
    this.transactionTypeSelect = this.select(/^Transaction Type/);

    this.searchInput = page.getByLabel(/^Search by Symbol or Name/);
    this.suggestions = page.getByRole('option');
    this.symbolInput = page.getByLabel(/^Symbol/);
    this.nameInput = page.getByLabel(/^Name/);

    this.quantityInput = page.getByLabel(/^Quantity/);
    this.priceInput = page.getByLabel(/^Price/);
    this.dateInput = page.getByLabel(/^Date/);

    this.bondModeSelect = this.select(/^Bond Entry Mode/);
    this.bondTypeSelect = this.select(/^Bond Type/);
    this.bondSeriesInput = page.getByLabel(/^Bond Series/);
    this.maturityDateInput = page.getByLabel(/^Maturity Date/);
    this.interestRateTypeSelect = this.select(/^Interest Rate Type/);
    this.interestRateInput = page.getByLabel(/^Interest Rate \(%\)/);
    this.wiborMarginInput = page.getByLabel(/^WIBOR Margin/);
    this.baseInterestRateInput = page.getByLabel(/^Base Interest Rate/);
    this.inflationMarginInput = page.getByLabel(/^Inflation Margin/);
    this.faceValueInput = page.getByLabel(/^Face Value/);
  }

  private select(label: RegExp): Locator {
    return this.page
      .locator('.MuiFormControl-root')
      .filter({ has: this.page.locator('label', { hasText: label }) })
      .getByRole('combobox');
  }

  private async choose(select: Locator, option: string | RegExp) {
    await select.click();
    const name = typeof option === 'string' ? { name: option, exact: true } : { name: option };
    await this.page.getByRole('option', name).click();
  }

  async goto() {
    await this.page.goto('/addStock');
    await expect(this.heading).toBeVisible();
  }

  async selectAssetType(type: AssetType) {
    await this.choose(this.assetTypeSelect, type);
  }

  async selectTransactionType(type: TransactionType) {
    await this.choose(this.transactionTypeSelect, type);
  }

  /** Bonds only: 'Search from Database' or 'Enter Manually'. */
  async selectBondMode(mode: 'Search from Database' | 'Enter Manually') {
    await this.choose(this.bondModeSelect, mode);
  }

  /** Types into the search box and picks the suggestion containing `optionText`. */
  async searchAndSelect(query: string, optionText: string | RegExp = query) {
    await this.searchInput.fill(query);
    await this.page.getByRole('option').filter({ hasText: optionText }).first().click();
    // Picking a suggestion locks the symbol/name fields.
    await expect(this.nameInput).toBeDisabled();
  }

  /**
   * Enters an asset by hand instead of picking a suggestion. The search box
   * is a required field, so it is filled too.
   */
  async enterAssetManually(symbol: string, name: string) {
    await this.searchInput.fill(symbol);
    await this.symbolInput.fill(symbol);
    await this.nameInput.fill(name);
  }

  /**
   * Bonds only: fills the "Enter Manually" form (fixed-rate bonds).
   * `bondType` is the code, e.g. 'TOS' or 'ROS'.
   */
  async enterBondManually(bond: {
    name: string;
    bondType: string;
    /** ISO date, e.g. '2035-12-31'. */
    maturityDate: string;
    interestRate: number | string;
  }) {
    await this.selectBondMode('Enter Manually');
    await this.choose(this.bondTypeSelect, new RegExp(`^${bond.bondType} - `));
    await this.nameInput.fill(bond.name);
    await this.maturityDateInput.fill(bond.maturityDate);
    await this.interestRateInput.fill(String(bond.interestRate));
  }

  /**
   * Full flow for a stock or crypto: opens the form, enters the asset by hand,
   * submits and waits for the success alert + redirect.
   */
  async addManualAsset(
    type: 'Stocks' | 'Cryptocurrencies',
    asset: { symbol: string; name: string },
    tx: TransactionDetails
  ) {
    await this.goto();
    if (type !== 'Stocks') await this.selectAssetType(type);
    await this.enterAssetManually(asset.symbol, asset.name);
    await this.fillTransaction(tx);
    await this.expectSuccess();
  }

  async fillTransaction({ quantity, type, price, date }: TransactionDetails) {
    await this.quantityInput.fill(String(quantity));
    if (type) await this.selectTransactionType(type);
    if (price !== undefined) await this.priceInput.fill(String(price));
    if (date) await this.dateInput.fill(date);
  }

  /** Clicks submit without waiting for anything (use when validation should block it). */
  async submit() {
    await this.submitButton.click();
  }

  /**
   * Clicks submit and returns the text of the alert() the page raises on
   * success ("Asset added successfully") or failure ("Error: ...").
   */
  async submitAndGetAlert(): Promise<string> {
    const dialogPromise = this.page.waitForEvent('dialog');
    await this.submitButton.click();
    const dialog = await dialogPromise;
    const message = dialog.message();
    await dialog.accept();
    return message;
  }

  async expectSuccess() {
    expect(await this.submitAndGetAlert()).toBe('Asset added successfully');
    await expect(this.page).toHaveURL('/');
  }
}
