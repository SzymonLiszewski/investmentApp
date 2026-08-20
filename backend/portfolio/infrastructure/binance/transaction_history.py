"""
Parse Binance "Transaction History" XLSX statements to normalized import rows.

The export is a single-sheet ledger of balance changes (columns: User ID, Time,
Account, Operation, Coin, Change, Remark) with leading metadata rows; the parser
locates the header row automatically. Trades appear as *groups* of ledger legs:

- ``Buy Crypto With Fiat`` / ``Buy Crypto With Card`` (and sell mirrors): one leg
  with a negative fiat change (money spent) and one with a positive crypto change
  (asset bought), logged a few seconds apart. Legs are matched by nearest
  timestamp within a tolerance.
- Spot/margin trades: ``Transaction Buy`` (+base) with ``Transaction Spend``
  (-quote), and ``Transaction Sold`` (-base) with ``Transaction Revenue``
  (+quote). All legs of one trade share the exact timestamp and account;
  multi-fill orders appear as several legs at the same second and are
  aggregated into a single row with the weighted-average price. When the
  quote leg is itself a non-cash cryptocurrency, a companion transaction on
  the opposite side is emitted for it too, so both legs of the trade are
  imported.
- ``Binance Convert``: one negative and one positive leg at the same timestamp,
  emitted as a SELL of the outgoing coin and/or a BUY of the incoming coin.

Stablecoins (USDT, BUSD, ...) are treated as *cash*, like fiat: acquiring or
spending them is not itself a portfolio transaction, and a trade quoted in a
stablecoin is priced in USD (1:1). Trades quoted in another cryptocurrency are
emitted with ``price=None`` so the import service resolves a market price for
the trade date. Everything else in the ledger (interest, rewards, fees, dust
sweeps, margin loans, deposits, withdrawals, transfers) is skipped.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from portfolio.services.transaction_import_service import NormalizedTransactionImportRow

logger = logging.getLogger(__name__)

FileArg = Union[str, Path, BytesIO, BinaryIO]

_REQUIRED_HEADERS = frozenset({"time", "operation", "coin", "change"})
_OPTIONAL_HEADERS = frozenset({"account"})

# Binance ``Operation`` values for fiat buy/sell trades (two legs paired by sign).
_FIAT_BUY_OPERATIONS = frozenset(
    {
        "buy crypto with fiat",
        "buy crypto with card",
        "buy crypto",
    }
)
_FIAT_SELL_OPERATIONS = frozenset(
    {
        "sell crypto with fiat",
        "sell crypto with card",
        "sell crypto to fiat",
        "sell crypto for fiat",
        "sell crypto",
    }
)

# Spot/margin trade legs: operation -> (side, role of the leg in the trade).
_SPOT_OPERATIONS = {
    "transaction buy": ("BUY", "base"),
    "transaction spend": ("BUY", "quote"),
    "transaction sold": ("SELL", "base"),
    "transaction revenue": ("SELL", "quote"),
}

_CONVERT_OPERATION = "binance convert"

_ALL_TRADE_OPERATIONS = (
    _FIAT_BUY_OPERATIONS
    | _FIAT_SELL_OPERATIONS
    | frozenset(_SPOT_OPERATIONS)
    | frozenset({_CONVERT_OPERATION})
)

# Coins treated as cash rather than portfolio assets. USD-pegged stablecoins
# map to USD (1:1); fiat currency codes map to themselves.
_STABLECOIN_CURRENCY = {
    "USDT": "USD",
    "BUSD": "USD",
    "USDC": "USD",
    "FDUSD": "USD",
    "TUSD": "USD",
    "USDP": "USD",
    "DAI": "USD",
}
_FIAT_CURRENCIES = frozenset(
    {"USD", "EUR", "GBP", "PLN", "CHF", "CZK", "RON", "HUF", "SEK", "NOK", "DKK",
     "AUD", "CAD", "JPY", "TRY", "UAH", "BRL", "ZAR", "NGN", "ARS", "MXN"}
)

# Max clock distance between the fiat leg and the crypto leg of one fiat trade.
_PAIR_TOLERANCE_SECONDS = 120


@dataclass
class _Leg:
    excel_row: int
    moment: datetime
    operation_key: str
    account: str
    coin: str
    change: float
    raw_change: str


def parse_binance_transaction_history_xlsx(
    file: FileArg,
    *,
    sheet_name: Optional[str] = None,
) -> List[NormalizedTransactionImportRow]:
    """
    Read a Binance Transaction History ``.xlsx`` statement and return rows for
    buy/sell trades reconstructed from their ledger legs.

    :param file: Path or binary file-like object (``bytes`` buffer seekable at 0).
    :param sheet_name: Override sheet title (default: first sheet with a
        recognizable Time/Operation/Coin/Change header row).
    """
    wb = load_workbook(file, read_only=False, data_only=True)
    try:
        ws, header_row_idx, col_map = _locate_ledger(wb, sheet_name)
        legs = _collect_trade_legs(ws, header_row_idx, col_map)
    finally:
        wb.close()

    out: List[NormalizedTransactionImportRow] = []
    out.extend(_rows_from_fiat_trades(legs))
    out.extend(_rows_from_spot_trades(legs))
    out.extend(_rows_from_converts(legs))
    out.sort(key=lambda r: r.source_row_index or 0)
    return out


def _locate_ledger(wb, sheet_name: Optional[str]) -> Tuple[Worksheet, int, dict]:
    if sheet_name:
        target = sheet_name.casefold().strip()
        candidates = [wb[n] for n in wb.sheetnames if n.casefold().strip() == target]
        if not candidates:
            raise ValueError(
                f'Workbook has no sheet named "{sheet_name}" (available: {wb.sheetnames!r})'
            )
    else:
        candidates = [wb[n] for n in wb.sheetnames]

    for ws in candidates:
        header_row_idx, col_map = _find_header_row(ws)
        if header_row_idx is not None and col_map is not None:
            return ws, header_row_idx, col_map
    raise ValueError(
        "Could not find a header row with Time, Operation, Coin, Change. "
        "Expected a Binance Transaction History export."
    )


def _find_header_row(ws: Worksheet) -> Tuple[Optional[int], Optional[dict]]:
    max_scan = 80
    for idx, row in enumerate(ws.iter_rows(min_row=1, max_row=max_scan), start=1):
        lowered_set = frozenset(
            str(c.value).strip().casefold()
            for c in row
            if c.value is not None and str(c.value).strip()
        )
        if not lowered_set:
            continue
        if _REQUIRED_HEADERS.issubset(lowered_set):
            col_map = {}
            for cell in row:
                if cell.value is None:
                    continue
                key = str(cell.value).strip().casefold()
                if key in _REQUIRED_HEADERS or key in _OPTIONAL_HEADERS:
                    col_map[key] = cell.column - 1
            return idx, col_map
    return None, None


def _parse_binance_number(raw) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    s = str(raw).strip().replace("\xa0", " ").replace(" ", "")
    if not s or s.lower() == "nan":
        return None
    negative = s.startswith("-")
    if negative:
        s = s[1:]
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def _parse_ledger_datetime(raw) -> Optional[datetime]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, date):
        return datetime(raw.year, raw.month, raw.day)
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _get_cell(row_values: List, col_idx: Optional[int]):
    if col_idx is None or col_idx >= len(row_values):
        return None
    return row_values[col_idx]


def _cash_currency(coin: str) -> Optional[str]:
    """Return the currency code if ``coin`` is cash-like (stablecoin/fiat), else None."""
    if coin in _STABLECOIN_CURRENCY:
        return _STABLECOIN_CURRENCY[coin]
    if coin in _FIAT_CURRENCIES:
        return coin
    return None


def _collect_trade_legs(
    ws: Worksheet,
    header_row_idx: int,
    col_map: dict,
) -> List[_Leg]:
    legs: List[_Leg] = []
    excel_row = header_row_idx
    for row in ws.iter_rows(min_row=header_row_idx + 1):
        excel_row += 1
        row_values = [c.value for c in row]

        operation_raw = _get_cell(row_values, col_map.get("operation"))
        operation_key = "" if operation_raw is None else str(operation_raw).strip().casefold()
        if operation_key not in _ALL_TRADE_OPERATIONS:
            continue

        time_raw = _get_cell(row_values, col_map.get("time"))
        moment = _parse_ledger_datetime(time_raw)
        if moment is None:
            logger.debug("Binance import: skip row %s — bad time %r", excel_row, time_raw)
            continue

        coin_raw = _get_cell(row_values, col_map.get("coin"))
        coin = "" if coin_raw is None else str(coin_raw).strip().upper()
        if not coin:
            logger.debug("Binance import: skip row %s — missing coin", excel_row)
            continue

        change_raw = _get_cell(row_values, col_map.get("change"))
        change = _parse_binance_number(change_raw)
        if change is None or change == 0:
            logger.debug(
                "Binance import: skip row %s — unparsable change %r", excel_row, change_raw
            )
            continue

        account_raw = _get_cell(row_values, col_map.get("account"))
        account = "" if account_raw is None else str(account_raw).strip()

        legs.append(
            _Leg(
                excel_row=excel_row,
                moment=moment,
                operation_key=operation_key,
                account=account,
                coin=coin,
                change=change,
                raw_change=str(change_raw).strip(),
            )
        )
    return legs


def _make_row(
    *,
    side: str,
    coin: str,
    quantity: float,
    price: Optional[float],
    currency: Optional[str],
    moment: datetime,
    excel_row: int,
    id_suffix: str,
    account: str,
    operation: str,
) -> NormalizedTransactionImportRow:
    time_str = moment.strftime("%Y-%m-%d %H:%M:%S")
    return NormalizedTransactionImportRow(
        transaction_type=side,
        quantity=quantity,
        price=price,
        trade_date=moment.date(),
        source_row_index=excel_row,
        symbol=coin,
        name=None,
        asset_type="cryptocurrencies",
        external_id=f"binance:{account}:{operation}:{time_str}:{coin}:{id_suffix}",
        currency=currency,
    )


# ---------------------------------------------------------------------------
# Fiat buys/sells (Buy Crypto With Fiat / Card): pair legs by sign and time.
# ---------------------------------------------------------------------------

def _match_fiat_leg(
    crypto_leg: _Leg,
    fiat_legs: List[_Leg],
    used: set,
) -> Optional[_Leg]:
    best_idx = None
    best_delta = None
    for idx, fiat in enumerate(fiat_legs):
        if idx in used:
            continue
        if (
            fiat.account != crypto_leg.account
            or fiat.operation_key != crypto_leg.operation_key
        ):
            continue
        delta = abs((fiat.moment - crypto_leg.moment).total_seconds())
        if delta > _PAIR_TOLERANCE_SECONDS:
            continue
        if best_delta is None or delta < best_delta:
            best_idx, best_delta = idx, delta
    if best_idx is None:
        return None
    used.add(best_idx)
    return fiat_legs[best_idx]


def _rows_from_fiat_trades(legs: List[_Leg]) -> List[NormalizedTransactionImportRow]:
    # For buys the crypto leg is the positive change (asset received) and the
    # fiat leg is negative (money spent); for sells the signs are flipped.
    out: List[NormalizedTransactionImportRow] = []
    for side, operations, crypto_sign in (
        ("BUY", _FIAT_BUY_OPERATIONS, 1),
        ("SELL", _FIAT_SELL_OPERATIONS, -1),
    ):
        side_legs = [l for l in legs if l.operation_key in operations]
        crypto_legs = [l for l in side_legs if l.change * crypto_sign > 0]
        fiat_legs = [l for l in side_legs if l.change * crypto_sign < 0]
        used: set = set()
        for crypto_leg in crypto_legs:
            if _cash_currency(crypto_leg.coin):
                logger.debug(
                    "Binance import: skip row %s — %s of cash-like coin %s",
                    crypto_leg.excel_row,
                    side,
                    crypto_leg.coin,
                )
                continue
            quantity = abs(crypto_leg.change)
            fiat_leg = _match_fiat_leg(crypto_leg, fiat_legs, used)
            price: Optional[float] = None
            currency: Optional[str] = None
            if fiat_leg is not None:
                price = abs(fiat_leg.change) / quantity
                currency = _cash_currency(fiat_leg.coin) or fiat_leg.coin
            else:
                logger.debug(
                    "Binance import: no fiat leg for row %s (%s %s) — price left to resolve",
                    crypto_leg.excel_row,
                    side,
                    crypto_leg.coin,
                )
            out.append(
                _make_row(
                    side=side,
                    coin=crypto_leg.coin,
                    quantity=quantity,
                    price=price,
                    currency=currency,
                    moment=crypto_leg.moment,
                    excel_row=crypto_leg.excel_row,
                    id_suffix=crypto_leg.raw_change,
                    account=crypto_leg.account,
                    operation=crypto_leg.operation_key,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Spot/margin trades (Transaction Buy/Spend/Sold/Revenue): group by account and
# exact timestamp; aggregate multi-fill legs into one row per base coin.
# ---------------------------------------------------------------------------

def _rows_from_spot_trades(legs: List[_Leg]) -> List[NormalizedTransactionImportRow]:
    groups = defaultdict(lambda: {"base": [], "quote": []})
    for leg in legs:
        mapped = _SPOT_OPERATIONS.get(leg.operation_key)
        if not mapped:
            continue
        side, role = mapped
        groups[(leg.account, leg.moment, side)][role].append(leg)

    out: List[NormalizedTransactionImportRow] = []
    for (account, moment, side), roles in groups.items():
        base_legs, quote_legs = roles["base"], roles["quote"]
        if not base_legs:
            continue
        base_coins = {l.coin for l in base_legs}
        quote_coins = {l.coin for l in quote_legs}

        # Price is only unambiguous when the group is a single trading pair.
        priced = len(base_coins) == 1 and len(quote_coins) == 1
        if not priced and quote_legs:
            logger.debug(
                "Binance import: ambiguous trade group at %s (%s) — %r vs %r; "
                "prices left to resolve",
                moment,
                account,
                sorted(base_coins),
                sorted(quote_coins),
            )

        for coin in sorted(base_coins):
            coin_legs = [l for l in base_legs if l.coin == coin]
            if _cash_currency(coin):
                logger.debug(
                    "Binance import: skip rows %r — %s of cash-like coin %s",
                    [l.excel_row for l in coin_legs],
                    side,
                    coin,
                )
                continue
            quantity = sum(abs(l.change) for l in coin_legs)
            if quantity <= 0:
                continue
            price: Optional[float] = None
            currency: Optional[str] = None
            if priced:
                quote_coin = next(iter(quote_coins))
                currency = _cash_currency(quote_coin)
                if currency is not None:
                    total_quote = sum(abs(l.change) for l in quote_legs)
                    price = total_quote / quantity
            first = min(coin_legs, key=lambda l: l.excel_row)
            id_suffix = (
                first.raw_change
                if len(coin_legs) == 1
                else f"{quantity:.8f}x{len(coin_legs)}"
            )
            out.append(
                _make_row(
                    side=side,
                    coin=coin,
                    quantity=quantity,
                    price=price,
                    currency=currency,
                    moment=moment,
                    excel_row=first.excel_row,
                    id_suffix=id_suffix,
                    account=account,
                    operation=first.operation_key,
                )
            )

        # A quote leg denominated in another cryptocurrency (rather than cash)
        # is itself a portfolio asset being received/spent, so it needs its
        # own companion transaction on the opposite side — otherwise only
        # half of the trade would be imported.
        if priced and quote_legs:
            quote_coin = next(iter(quote_coins))
            if _cash_currency(quote_coin) is None:
                quote_coin_legs = [l for l in quote_legs if l.coin == quote_coin]
                quantity = sum(abs(l.change) for l in quote_coin_legs)
                if quantity > 0:
                    first = min(quote_coin_legs, key=lambda l: l.excel_row)
                    id_suffix = (
                        first.raw_change
                        if len(quote_coin_legs) == 1
                        else f"{quantity:.8f}x{len(quote_coin_legs)}"
                    )
                    out.append(
                        _make_row(
                            side="SELL" if side == "BUY" else "BUY",
                            coin=quote_coin,
                            quantity=quantity,
                            price=None,
                            currency=None,
                            moment=moment,
                            excel_row=first.excel_row,
                            id_suffix=id_suffix,
                        )
                    )
    return out


# ---------------------------------------------------------------------------
# Binance Convert: one negative and one positive leg at the same timestamp —
# a SELL of the outgoing coin and/or a BUY of the incoming coin.
# ---------------------------------------------------------------------------

def _rows_from_converts(legs: List[_Leg]) -> List[NormalizedTransactionImportRow]:
    groups = defaultdict(list)
    for leg in legs:
        if leg.operation_key == _CONVERT_OPERATION:
            groups[(leg.account, leg.moment)].append(leg)

    out: List[NormalizedTransactionImportRow] = []
    for (account, moment), group in groups.items():
        negatives = [l for l in group if l.change < 0]
        positives = [l for l in group if l.change > 0]
        if len(negatives) != 1 or len(positives) != 1:
            logger.debug(
                "Binance import: skip convert group at %s (%s) — unexpected legs %r",
                moment,
                account,
                [l.excel_row for l in group],
            )
            continue
        neg, pos = negatives[0], positives[0]
        neg_cash = _cash_currency(neg.coin)
        pos_cash = _cash_currency(pos.coin)

        if pos_cash is None:
            out.append(
                _make_row(
                    side="BUY",
                    coin=pos.coin,
                    quantity=abs(pos.change),
                    price=(abs(neg.change) / abs(pos.change)) if neg_cash else None,
                    currency=neg_cash,
                    moment=moment,
                    excel_row=pos.excel_row,
                    id_suffix=pos.raw_change,
                    account=account,
                    operation=pos.operation_key,
                )
            )
        if neg_cash is None:
            out.append(
                _make_row(
                    side="SELL",
                    coin=neg.coin,
                    quantity=abs(neg.change),
                    price=(abs(pos.change) / abs(neg.change)) if pos_cash else None,
                    currency=pos_cash,
                    moment=moment,
                    excel_row=neg.excel_row,
                    id_suffix=neg.raw_change,
                    account=account,
                    operation=neg.operation_key,
                )
            )
    return out
