from datetime import date
from io import BytesIO

from django.test import SimpleTestCase
from openpyxl import Workbook

from portfolio.infrastructure.binance import parse_binance_transaction_history_xlsx


def _build_workbook(rows, *, header=True):
    """
    Mimic the real Binance statement layout: metadata rows at the top, then the
    ledger header, then balance-change rows (User ID left empty like the export).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet0"
    ws.append(["", "www.binance.com"])
    ws.append(["Transaction History"])
    ws.append([])
    if header:
        ws.append(["User ID", "Time", "Account", "Operation", "Coin", "Change", "Remark"])
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


class ParseBinanceTransactionHistoryTests(SimpleTestCase):
    def test_parses_buy_pair_into_single_buy_row(self):
        buf = _build_workbook(
            [
                ["", "2026-06-13 20:18:28", "Spot", "Buy Crypto With Fiat", "PLN", "-990.86", ""],
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "BTC", "0.00419071", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "BUY")
        self.assertEqual(row.symbol, "BTC")
        self.assertEqual(row.asset_type, "cryptocurrencies")
        self.assertEqual(row.trade_date, date(2026, 6, 13))
        self.assertAlmostEqual(row.quantity, 0.00419071)
        self.assertAlmostEqual(row.price, 990.86 / 0.00419071)
        self.assertEqual(row.currency, "PLN")
        self.assertEqual(row.external_id, "binance:2026-06-13 20:18:34:BTC:0.00419071")

    def test_parses_sell_pair_into_single_sell_row(self):
        buf = _build_workbook(
            [
                ["", "2026-06-14 10:00:01", "Spot", "Sell Crypto With Fiat", "BTC", "-0.001", ""],
                ["", "2026-06-14 10:00:05", "Spot", "Sell Crypto With Fiat", "PLN", "350.20", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "SELL")
        self.assertEqual(row.symbol, "BTC")
        self.assertAlmostEqual(row.quantity, 0.001)
        self.assertAlmostEqual(row.price, 350.20 / 0.001)
        self.assertEqual(row.currency, "PLN")

    def test_skips_non_trade_operations(self):
        buf = _build_workbook(
            [
                ["", "2026-01-01 07:54:33", "Spot", "Simple Earn Flexible Interest", "ETH", "0.00000005", ""],
                ["", "2026-04-20 19:53:33", "Funding", "Withdraw", "ETH", "-0.002", ""],
                ["", "2026-06-13 20:05:48", "Spot", "Deposit", "PLN", "990", ""],
                ["", "2026-02-26 04:46:40", "Spot", "Airdrop Assets", "SXT", "7.02042298", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(rows, [])

    def test_unpaired_crypto_leg_gets_no_price(self):
        buf = _build_workbook(
            [
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "BTC", "0.00419071", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].transaction_type, "BUY")
        self.assertIsNone(rows[0].price)
        self.assertIsNone(rows[0].currency)

    def test_fiat_leg_outside_tolerance_is_not_paired(self):
        buf = _build_workbook(
            [
                ["", "2026-06-13 10:00:00", "Spot", "Buy Crypto With Fiat", "PLN", "-990.86", ""],
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "BTC", "0.00419071", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0].price)

    def test_two_buys_pair_with_nearest_fiat_leg(self):
        buf = _build_workbook(
            [
                ["", "2026-06-13 20:18:28", "Spot", "Buy Crypto With Fiat", "PLN", "-990.86", ""],
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "BTC", "0.00419071", ""],
                ["", "2026-06-13 21:00:00", "Spot", "Buy Crypto With Fiat", "PLN", "-500", ""],
                ["", "2026-06-13 21:00:03", "Spot", "Buy Crypto With Fiat", "ETH", "0.05", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 2)
        by_symbol = {r.symbol: r for r in rows}
        self.assertAlmostEqual(by_symbol["BTC"].price, 990.86 / 0.00419071)
        self.assertAlmostEqual(by_symbol["ETH"].price, 500 / 0.05)

    def test_skips_unparsable_rows_without_raising(self):
        buf = _build_workbook(
            [
                ["", "not-a-date", "Spot", "Buy Crypto With Fiat", "BTC", "0.001", ""],
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "", "0.001", ""],
                ["", "2026-06-13 20:18:34", "Spot", "Buy Crypto With Fiat", "BTC", "abc", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(rows, [])

    def test_buying_stablecoin_with_card_is_skipped_as_cash(self):
        buf = _build_workbook(
            [
                ["", "2021-10-07 16:26:43", "Spot", "Fiat OCBS - Add Fiat and Fees", "PLN", "147.15", ""],
                ["", "2021-10-07 16:26:44", "Spot", "Buy Crypto With Card", "PLN", "-147.15", ""],
                ["", "2021-10-07 16:26:44", "Spot", "Buy Crypto With Card", "USDT", "36.16180626", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(rows, [])

    def test_buy_crypto_with_card_of_non_stablecoin_is_imported(self):
        buf = _build_workbook(
            [
                ["", "2021-10-07 16:26:44", "Spot", "Buy Crypto With Card", "PLN", "-147.15", ""],
                ["", "2021-10-07 16:26:44", "Spot", "Buy Crypto With Card", "BNB", "0.35", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].transaction_type, "BUY")
        self.assertEqual(rows[0].symbol, "BNB")
        self.assertAlmostEqual(rows[0].price, 147.15 / 0.35)
        self.assertEqual(rows[0].currency, "PLN")

    def test_spot_trade_buy_priced_in_usd_from_usdt_quote(self):
        buf = _build_workbook(
            [
                ["", "2021-10-07 16:46:02", "Spot", "Transaction Buy", "BNB", "0.023", ""],
                ["", "2021-10-07 16:46:02", "Spot", "Transaction Spend", "USDT", "-10.1223", ""],
                ["", "2021-10-07 16:46:02", "Spot", "Transaction Fee", "BNB", "-0.00001725", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "BUY")
        self.assertEqual(row.symbol, "BNB")
        self.assertAlmostEqual(row.quantity, 0.023)
        self.assertAlmostEqual(row.price, 10.1223 / 0.023)
        self.assertEqual(row.currency, "USD")

    def test_spot_trade_multi_fill_aggregates_into_one_row(self):
        buf = _build_workbook(
            [
                ["", "2021-10-11 21:54:57", "Cross Margin", "Transaction Buy", "BTC", "0.00001", ""],
                ["", "2021-10-11 21:54:57", "Cross Margin", "Transaction Buy", "BTC", "0.00056", ""],
                ["", "2021-10-11 21:54:57", "Cross Margin", "Transaction Spend", "USDT", "-0.5754194", ""],
                ["", "2021-10-11 21:54:57", "Cross Margin", "Transaction Spend", "USDT", "-32.223492", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "BUY")
        self.assertAlmostEqual(row.quantity, 0.00057)
        self.assertAlmostEqual(row.price, (0.5754194 + 32.223492) / 0.00057)
        self.assertEqual(row.currency, "USD")

    def test_spot_sell_with_crypto_quote_gets_no_price(self):
        buf = _build_workbook(
            [
                ["", "2021-10-11 22:29:43", "Spot", "Transaction Sold", "BNB", "-0.015", ""],
                ["", "2021-10-11 22:29:43", "Spot", "Transaction Revenue", "BTC", "0.00010681", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "SELL")
        self.assertEqual(row.symbol, "BNB")
        self.assertAlmostEqual(row.quantity, 0.015)
        self.assertIsNone(row.price)
        self.assertIsNone(row.currency)

    def test_spot_sell_priced_in_usd(self):
        buf = _build_workbook(
            [
                ["", "2021-10-13 15:52:21", "Spot", "Transaction Sold", "XRP", "-59", ""],
                ["", "2021-10-13 15:52:21", "Spot", "Transaction Revenue", "USDT", "63.9442", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "SELL")
        self.assertEqual(row.symbol, "XRP")
        self.assertAlmostEqual(row.price, 63.9442 / 59)
        self.assertEqual(row.currency, "USD")

    def test_convert_from_stablecoin_is_a_priced_buy(self):
        buf = _build_workbook(
            [
                ["", "2023-07-24 15:31:17", "Spot", "Binance Convert", "BTC", "0.00011613", ""],
                ["", "2023-07-24 15:31:17", "Spot", "Binance Convert", "USDT", "-3.39876373", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "BUY")
        self.assertEqual(row.symbol, "BTC")
        self.assertAlmostEqual(row.price, 3.39876373 / 0.00011613)
        self.assertEqual(row.currency, "USD")

    def test_convert_to_stablecoin_is_a_priced_sell(self):
        buf = _build_workbook(
            [
                ["", "2023-08-05 01:11:00", "Spot", "Binance Convert", "STMX", "-1056.14387376", ""],
                ["", "2023-08-05 01:11:00", "Spot", "Binance Convert", "USDT", "7.70985027", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.transaction_type, "SELL")
        self.assertEqual(row.symbol, "STMX")
        self.assertAlmostEqual(row.quantity, 1056.14387376)
        self.assertAlmostEqual(row.price, 7.70985027 / 1056.14387376)
        self.assertEqual(row.currency, "USD")

    def test_crypto_to_crypto_convert_emits_sell_and_buy_without_price(self):
        buf = _build_workbook(
            [
                ["", "2023-07-24 15:31:00", "Spot", "Binance Convert", "BTC", "0.00024211", ""],
                ["", "2023-07-24 15:31:00", "Spot", "Binance Convert", "ETH", "-0.00382282", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(len(rows), 2)
        by_type = {r.transaction_type: r for r in rows}
        self.assertEqual(by_type["BUY"].symbol, "BTC")
        self.assertAlmostEqual(by_type["BUY"].quantity, 0.00024211)
        self.assertIsNone(by_type["BUY"].price)
        self.assertEqual(by_type["SELL"].symbol, "ETH")
        self.assertAlmostEqual(by_type["SELL"].quantity, 0.00382282)
        self.assertIsNone(by_type["SELL"].price)

    def test_non_trade_ledger_operations_stay_skipped(self):
        buf = _build_workbook(
            [
                ["", "2021-10-08 15:24:29", "Spot", "Small Assets Exchange BNB", "SHIB", "-705.34", ""],
                ["", "2021-10-08 15:24:29", "Spot", "Small Assets Exchange BNB", "BNB", "0.00003779", ""],
                ["", "2021-10-07 19:21:16", "Spot", "Liquid Swap Add/Sell", "USDT", "-13.2302", ""],
                ["", "2021-10-13 19:13:52", "Cross Margin", "Margin Loan", "USDT", "100", ""],
                ["", "2022-01-01 00:00:00", "Spot", "BNB Vault Rewards", "BNB", "0.0001", ""],
                ["", "2022-01-02 00:00:00", "Spot", "Inter-Wallet Transfer", "BTC", "-0.01", ""],
            ]
        )
        rows = parse_binance_transaction_history_xlsx(buf)
        self.assertEqual(rows, [])

    def test_missing_header_raises_value_error(self):
        buf = _build_workbook([], header=False)
        with self.assertRaises(ValueError):
            parse_binance_transaction_history_xlsx(buf)

    def test_missing_named_sheet_raises_value_error(self):
        buf = _build_workbook([])
        with self.assertRaises(ValueError):
            parse_binance_transaction_history_xlsx(buf, sheet_name="Nope")
