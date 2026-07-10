---
name: new-import-parser
description: Scaffold a new broker/file-format parser for the transaction import pipeline — parser module → view → URL → frontend broker card → tests. Use when adding support for importing transactions from a new broker's export file.
---

# Add a new transaction-import parser

Follow every step in order. The architecture rule: parsers are plain functions that map broker-specific rows into `NormalizedTransactionImportRow` (defined in `backend/portfolio/services/transaction_import_service.py`). A parser must never touch the database, import Django models, or call `import_normalized_transactions()` itself — persistence is the view's job. There is no interface/provider/factory DI layer here; that pattern is reserved for live external data APIs (see `new-fetcher`), not one-shot file parsing.

## 0. Gather requirements

Before writing code, establish (ask the user if not stated):
- **Broker name** — e.g. `revolut`, `ibkr`. Determines the infrastructure subpackage, URL segment, and `external_id` prefix.
- **File format** — `.xlsx` (via `openpyxl`) or `.csv`, and the sheet name if XLSX has multiple sheets.
- **Column/field mapping** — which raw columns map to which `NormalizedTransactionImportRow` field (`transaction_type`, `quantity`, `price`, `trade_date`, `symbol`/`name`/`product_id`, `currency`, `external_id`, and any bond-specific fields).
- **Buy/sell detection** — an explicit type column with known values, or free-text parsing (e.g. XTB's comment regex `OPEN/CLOSE BUY/SELL <qty> @ <price>` in `cash_operations.py`'s `_COMMENT_TRADE`).
- **External ID source** — the raw field that uniquely identifies a row at the broker (transaction/order ID). Always prefix it `"<broker>:"` in the output row to avoid cross-broker collisions.

## 1. Parser module

Create `backend/portfolio/infrastructure/<broker>/<format_or_sheet>.py`, modeled on `backend/portfolio/infrastructure/xtb/cash_operations.py`:
- Module docstring describing the source file/sheet.
- Public function `parse_<broker>_<format>(file, *, sheet_name=None) -> List[NormalizedTransactionImportRow]` (`FileArg = Union[str, Path, BytesIO, BinaryIO]`), importing `NormalizedTransactionImportRow` from `portfolio.services.transaction_import_service`.
- If XLSX: locate the header row dynamically (see `_find_header_row`) rather than assuming a fixed row number — broker exports often have leading metadata rows.
- Private helpers for locale-aware number parsing (see `_parse_xtb_number` — handles `,`/`.` as decimal vs. thousands separator) and date parsing (see `_parse_trade_datetime`).
- **Skip, don't raise, per-row**: rows that aren't trades, or that fail to parse (bad date, unparsable amount, missing symbol/ID), should be skipped with a `logger.debug(...)` call and `continue` — never let one bad row abort the whole import.
- **Raise `ValueError` only for structural problems**: missing sheet, or no recognizable header row — the view maps this to a 400 for the whole upload.

## 2. Package export

Create `backend/portfolio/infrastructure/<broker>/__init__.py` (or add to it if the broker package already exists):

```python
from .<format_or_sheet> import parse_<broker>_<format>

__all__ = ["parse_<broker>_<format>"]
```

Matches `backend/portfolio/infrastructure/xtb/__init__.py`.

## 3. View

Add a new `APIView` class to `backend/portfolio/views/transaction_import.py`, modeled on `XtbCashOperationsImportView` in the same file:

```python
class <Broker><Format>ImportView(APIView):
    """
    Upload a <broker> <format> export; import trade rows.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "No file provided. Use the field name 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = getattr(upload, "name", "") or ""
        if not str(name).lower().endswith(".<ext>"):
            return Response(
                {"detail": "Expected a file with extension .<ext>."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            upload.seek(0)
        except (AttributeError, OSError):
            pass

        try:
            rows = parse_<broker>_<format>(upload)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("<Broker> <format> parse failed")
            return Response(
                {"detail": "Could not read the file. Check that it is a valid <broker> export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = import_normalized_transactions(request.user, rows)
        outcomes = [
            {
                "source_row_index": o.source_row_index,
                "status": o.status,
                "transaction_id": o.transaction_id,
                "message": o.message,
            }
            for o in result.outcomes
        ]

        return Response(
            {
                "created_count": result.created_count,
                "parsed_row_count": len(rows),
                "outcomes": outcomes,
            },
            status=status.HTTP_200_OK,
        )
```

Add the import at the top of the file: `from portfolio.infrastructure.<broker> import parse_<broker>_<format>`.

## 4. View export

Add to `backend/portfolio/views/__init__.py`:

```python
from .transaction_import import XtbCashOperationsImportView, <Broker><Format>ImportView
```

## 5. URL registration

Add to `backend/portfolio/urls.py`, alongside the existing `import/xtb/` path:

```python
path(
    'import/<broker>/',
    views.<Broker><Format>ImportView.as_view(),
    name='portfolio_import_<broker>',
),
```

Resolves to `/api/portfolio/import/<broker>/` (the `api/portfolio/` prefix comes from `backend/backend/urls.py`).

## 6. Frontend wiring

In `frontend/src/pages/ImportTransactionsPage.jsx`:

- Add a broker card button in the `STEPS.BROKER` grid (copy the `chooseXtb` pattern):

```jsx
const choose<Broker> = () => {
  setSelectedBroker('<broker>');
  setStep(STEPS.UPLOAD);
  setError(null);
  setResult(null);
  setFile(null);
};
```

```jsx
<button type="button" className="importTxBrokerCard" onClick={choose<Broker>}>
  <span className="importTxBrokerName" style={{ color: "#000" }}><Broker Display Name></span>
  <span className="importTxBrokerDesc"><short format description></span>
</button>
```

- Add a `selectedBroker === '<broker>'` branch under `STEPS.UPLOAD` with instructions text (what export the user needs, which columns must be present) and a file input `accept` attribute matching the format.
- Add a `submit<Broker>` function that mirrors `submitXtb` — validates the extension client-side, builds `FormData`, POSTs to `/api/portfolio/import/<broker>/` with the same `transformRequest` header-stripping, and sets `result`/`error`.
- No new CSS needed — reuse the existing `importTx*` classes.

## 7. Tests

Create `backend/portfolio/tests/test_<broker>_<format>.py`. There's no existing parser-level test file to copy structurally, so build the fixture inline:

```python
from datetime import date
from io import BytesIO

from django.test import SimpleTestCase
from openpyxl import Workbook

from portfolio.infrastructure.<broker> import parse_<broker>_<format>


def _build_workbook(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "<Sheet Name>"
    ws.append(["Type", "Ticker", ...])  # header row matching the real export
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


class Parse<Broker><Format>Tests(SimpleTestCase):
    def test_parses_buy_row(self):
        buf = _build_workbook([[...]])
        rows = parse_<broker>_<format>(buf)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].transaction_type, "BUY")
        self.assertEqual(rows[0].external_id, "<broker>:<id>")

    def test_skips_non_trade_rows(self):
        ...

    def test_skips_unparsable_row_without_raising(self):
        ...
```

Use `SimpleTestCase` (no DB needed — parsers are pure). Cover: happy-path buy/sell mapping, non-trade rows skipped, malformed rows skipped without raising, `external_id` correctly prefixed. Don't duplicate `test_transaction_import_service.py` (that already covers the service layer) — only test the parser function itself.

## 8. Verify

```bash
DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test portfolio --no-input
```

On Windows/PowerShell:
```powershell
$env:DJANGO_SETTINGS_MODULE = 'backend.settings_test'; python manage.py test portfolio --no-input
```

Since the frontend was touched, also run from `frontend/`:
```bash
npm run lint
npm run test
```

Then start the dev server and manually walk the upload flow for the new broker: pick the broker card, upload a sample export, confirm `created_count`/`outcomes` render correctly, and re-upload the same file to confirm duplicates are skipped via `external_id`.

## Guardrails

- **Parsers stay pure** — no DB access, no Django model imports, no calls to `import_normalized_transactions()`. They must be unit-testable with `SimpleTestCase` and no test database.
- **Always prefix `external_id`** with `"<broker>:"` — this is what prevents the same raw broker ID from colliding across different brokers/parsers.
- **Skip-and-log per-row, raise only structurally** — a single unparsable trade row must never abort the whole file; missing sheet/headers should raise `ValueError` so the view can 400 the entire upload with a clear message.
- **Reuse `NormalizedTransactionImportRow` fields as-is** — if a broker exposes data the dataclass doesn't carry, extend the dataclass in `transaction_import_service.py` (and the row-processing logic that consumes it) rather than smuggling extra data through another channel.
- **Match the existing view's response shape** (`created_count`, `parsed_row_count`, `outcomes`) — the frontend result rendering in `ImportTransactionsPage.jsx` depends on this exact structure.
