import { test, expect } from './fixtures';
import { CurrencyCode } from './pages/PortfolioPage';
import { addTransactionViaApi } from './utils';
import { expectedPositionTexts, MOCK_PRICE_USD, MOCK_USD_RATE } from './mockData';

const APPLE = { symbol: 'AAPL', name: 'Apple Inc.' };
const BITCOIN = { symbol: 'BTC-USD', name: 'Bitcoin' };

test.describe('Portfolio - empty state', () => {
  test('a new user has no active positions', async ({ portfolioPage }) => {
    await portfolioPage.goto();

    await portfolioPage.expectNoPositions();
  });

  test('every dashboard section renders with its empty-state content', async ({ portfolioPage }) => {
    await portfolioPage.goto();
    await portfolioPage.waitForPositionsLoaded();

    await expect(portfolioPage.valueHistorySection).toContainText('No portfolio history available yet.');

    await expect(
      portfolioPage.compositionSection.getByRole('heading', { name: 'Allocation by asset', exact: true })
    ).toBeVisible();

    await expect(
      portfolioPage.assetClassSection.getByRole('heading', { name: 'Allocation by asset class' })
    ).toBeVisible();
    await expect(portfolioPage.assetClassSection).toContainText('No asset class data');

    for (const name of ['Sharpe Ratio', 'Sortino Ratio', 'Alpha']) {
      await expect(portfolioPage.indicatorsSection.getByText(name, { exact: true })).toBeVisible();
    }
    await expect(portfolioPage.indicatorsSection.getByText('No data')).toHaveCount(3);

    await expect(
      portfolioPage.positionsSection.getByRole('heading', { name: 'Active positions' })
    ).toBeVisible();
  });
});

// Positions are checked in USD: stocks/crypto are USD-native, so the numbers are
// the raw ones entered in the form and don't depend on FX. Currency conversion
// has its own test below.
test.describe('Portfolio - positions from transactions', () => {
  test('a buy creates a position with the correct cost basis and valuation', async ({
    addAssetPage,
    portfolioPage,
  }) => {
    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 10, price: 100 });

    await portfolioPage.gotoInCurrency('USD');

    // 10 × 100 = 1,000 cost; 10 × 188.86 (mock price) = 1,888.60 value.
    await expect(portfolioPage.positionCell('AAPL', 'asset')).toHaveText('Apple Inc.');
    await expect(portfolioPage.positionCell('AAPL', 'type')).toHaveText('Stock');
    await expect(portfolioPage.positionCell('AAPL', 'quantity')).toHaveText('10');
    await expect(portfolioPage.positionCell('AAPL', 'avgPrice')).toHaveText('100.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'totalCost')).toHaveText('1,000.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'currentValue')).toHaveText('1,888.60 USD');
    await expect(portfolioPage.positionCell('AAPL', 'profit')).toHaveText('888.60 USD');
    await expect(portfolioPage.positionCell('AAPL', 'returnPct')).toHaveText('+88.86%');
  });

  test('two buys of the same asset merge into one position at the weighted average price', async ({
    addAssetPage,
    portfolioPage,
  }) => {
    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 10, price: 100 });
    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 10, price: 200 });

    await portfolioPage.gotoInCurrency('USD');

    // (10 × 100 + 10 × 200) / 20 = 150 average; 3,000 cost; 20 × 188.86 = 3,777.20 value.
    await expect(portfolioPage.positionRow('AAPL')).toHaveCount(1);
    await expect(portfolioPage.positionCell('AAPL', 'quantity')).toHaveText('20');
    await expect(portfolioPage.positionCell('AAPL', 'avgPrice')).toHaveText('150.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'totalCost')).toHaveText('3,000.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'currentValue')).toHaveText('3,777.20 USD');
    await expect(portfolioPage.positionCell('AAPL', 'profit')).toHaveText('777.20 USD');
    await expect(portfolioPage.positionCell('AAPL', 'returnPct')).toHaveText('+25.91%');
  });

  test('a partial sell reduces the quantity but keeps the average purchase price', async ({
    addAssetPage,
    portfolioPage,
  }) => {
    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 10, price: 100 });
    // The sell price is deliberately different from the buy price: it must not
    // leak into the average cost of the remaining shares.
    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 4, type: 'Sell', price: 150 });

    await portfolioPage.gotoInCurrency('USD');

    // 6 shares left, still averaging 100 → 600 cost; 6 × 188.86 = 1,133.16 value.
    await expect(portfolioPage.positionRow('AAPL')).toHaveCount(1);
    await expect(portfolioPage.positionCell('AAPL', 'quantity')).toHaveText('6');
    await expect(portfolioPage.positionCell('AAPL', 'avgPrice')).toHaveText('100.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'totalCost')).toHaveText('600.00 USD');
    await expect(portfolioPage.positionCell('AAPL', 'currentValue')).toHaveText('1,133.16 USD');
    await expect(portfolioPage.positionCell('AAPL', 'profit')).toHaveText('533.16 USD');
    await expect(portfolioPage.positionCell('AAPL', 'returnPct')).toHaveText('+88.86%');
  });

  test('stocks, crypto and bonds show the right type and feed the asset class allocation', async ({
    page,
    addAssetPage,
    portfolioPage,
  }) => {
    // The crypto and bond forms are taller than a 720px viewport, and
    // .add-stocks-container is `position: fixed` (no scrolling), so the submit
    // button is unreachable at the default size. Use a tall viewport until the
    // form layout is fixed.
    await page.setViewportSize({ width: 1280, height: 2000 });

    const bondName = 'E2E Treasury Bond';

    await addAssetPage.addManualAsset('Stocks', APPLE, { quantity: 10, price: 100 });
    await addAssetPage.addManualAsset('Cryptocurrencies', BITCOIN, { quantity: 2, price: 100 });

    await addAssetPage.goto();
    await addAssetPage.selectAssetType('Bonds');
    await addAssetPage.enterBondManually({
      name: bondName,
      bondType: 'TOS',
      maturityDate: '2035-12-31',
      interestRate: 5,
    });
    await addAssetPage.fillTransaction({ quantity: 3, price: 100 });
    await addAssetPage.expectSuccess();

    // Default display currency (PLN). Stocks/crypto are USD-native → × 2.4;
    // a bond bought today is still worth its 100 PLN face value.
    await portfolioPage.goto();
    await portfolioPage.expectPosition('AAPL');
    await expect(portfolioPage.positionCell('AAPL', 'type')).toHaveText('Stock');
    await expect(portfolioPage.positionCell('BTC-USD', 'type')).toHaveText('Crypto');
    await expect(portfolioPage.positionCell(bondName, 'type')).toHaveText('Bond');
    await expect(portfolioPage.positionRow('AAPL')).toHaveCount(1);
    await expect(portfolioPage.positionRow('BTC-USD')).toHaveCount(1);
    await expect(portfolioPage.positionRow(bondName)).toHaveCount(1);

    const stocks = 10 * MOCK_PRICE_USD.AAPL * MOCK_USD_RATE.PLN;
    const crypto = 2 * MOCK_PRICE_USD['BTC-USD'] * MOCK_USD_RATE.PLN;
    const bonds = 3 * 100;
    const total = stocks + crypto + bonds;
    const pct = (value: number) => `${Math.round((value / total) * 100)}%`;

    await expect(portfolioPage.assetClassSection.getByText(`Stocks: ${pct(stocks)}`)).toBeVisible();
    await expect(portfolioPage.assetClassSection.getByText(`Cryptocurrencies: ${pct(crypto)}`)).toBeVisible();
    await expect(portfolioPage.assetClassSection.getByText(`Bonds: ${pct(bonds)}`)).toBeVisible();
  });
});

test.describe('Portfolio - currency selector', () => {
  const currencies = Object.keys(MOCK_USD_RATE) as CurrencyCode[];

  for (const currency of currencies) {
    test(`values are converted correctly when displayed in ${currency}`, async ({
      request,
      user,
      portfolioPage,
    }) => {
      // Both positions are USD-native; API setup keeps this test about display only.
      await addTransactionViaApi(request, user.tokens, {
        ...APPLE,
        assetType: 'stocks',
        quantity: 10,
        price: 100,
      });
      await addTransactionViaApi(request, user.tokens, {
        ...BITCOIN,
        assetType: 'cryptocurrencies',
        quantity: 2,
        price: 100,
      });

      await portfolioPage.gotoInCurrency(currency);

      const positions = [
        { symbol: 'AAPL', open: { quantity: 10, avgCostUsd: 100, priceUsd: MOCK_PRICE_USD.AAPL } },
        { symbol: 'BTC-USD', open: { quantity: 2, avgCostUsd: 100, priceUsd: MOCK_PRICE_USD['BTC-USD'] } },
      ];

      for (const { symbol, open } of positions) {
        const expected = expectedPositionTexts(open, currency);

        await expect(portfolioPage.positionCell(symbol, 'quantity')).toHaveText(expected.quantity);
        await expect(portfolioPage.positionCell(symbol, 'avgPrice')).toHaveText(expected.avgPrice);
        await expect(portfolioPage.positionCell(symbol, 'totalCost')).toHaveText(expected.totalCost);
        await expect(portfolioPage.positionCell(symbol, 'currentValue')).toHaveText(expected.currentValue);
        await expect(portfolioPage.positionCell(symbol, 'profit')).toHaveText(expected.profit);
        await expect(portfolioPage.positionCell(symbol, 'returnPct')).toHaveText(expected.returnPct);
      }
    });
  }
});
