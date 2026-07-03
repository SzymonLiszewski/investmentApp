from django.test import SimpleTestCase

from analytics.services.top_stocks import get_top_stock_symbols


class TopStocksLoaderTests(SimpleTestCase):
    def test_returns_curated_symbols(self):
        symbols = get_top_stock_symbols()
        self.assertGreaterEqual(len(symbols), 40)
        self.assertEqual(len(symbols), len(set(symbols)))
        for symbol in symbols:
            self.assertFalse(symbol.startswith("#"))
            self.assertEqual(symbol, symbol.upper())
            self.assertEqual(symbol, symbol.strip())
        self.assertIn("AAPL", symbols)

    def test_returns_a_copy(self):
        first = get_top_stock_symbols()
        first.append("MUTATED")
        self.assertNotIn("MUTATED", get_top_stock_symbols())
