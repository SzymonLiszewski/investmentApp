import os
from typing import List

_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "management",
    "commands",
    "data",
    "top_stocks.txt",
)

_cached_symbols: List[str] | None = None


def get_top_stock_symbols() -> List[str]:
    """Return the curated list of top stock symbols used for nightly training."""
    global _cached_symbols
    if _cached_symbols is None:
        symbols = []
        with open(_DATA_FILE, encoding="utf-8") as f:
            for line in f:
                symbol = line.strip().upper()
                if symbol and not symbol.startswith("#") and symbol not in symbols:
                    symbols.append(symbol)
        _cached_symbols = symbols
    return list(_cached_symbols)
