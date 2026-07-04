---
name: new-fetcher
description: Scaffold a new external data source (fetcher) following the interface/provider/factory DI pattern. Use when adding any new market-data, news, or similar external API integration.
---

# Add a new external data fetcher

Follow this checklist completely — every step, in order. The DI rule: domain code depends on an abstract interface; concrete providers are chosen only by a factory function based on settings flags. Views and services must never import a concrete provider.

## 0. Gather requirements

Before writing code, establish (ask the user if not stated):
- **Domain name** — what data is fetched (e.g. `commodity_data`, `dividends`). Determines interface and factory names.
- **Provider/source name** — the external service (e.g. AlphaVantage, yfinance).
- **Interface methods** — signatures and return shapes.
- **Key-gated?** — does the provider need an API key? This decides whether a NoOp variant and `*_API_ENABLED` flag are required.

## 1. Interface

Create `backend/base/infrastructure/interfaces/<domain>.py`, modeled on `economic_calendar.py` in the same directory: module docstring, class extending `ABC`, `@abstractmethod` methods with type hints and one-line docstrings.

Export it from `backend/base/infrastructure/interfaces/__init__.py` (import + `__all__` entry).

## 2. Concrete provider

Create `backend/base/infrastructure/providers/<source>.py` (or extend an existing provider module like `yfinance_fetchers.py` if the source is already used). The class implements the interface. If key-gated, take `api_key` via the constructor — see `AlphaVantageEconomicCalendarFetcher` in `providers/economic_calendar.py`.

## 3. Mock provider

Add `Mock<Domain>Fetcher` to `backend/base/infrastructure/providers/mock_fetchers.py`, matching the style of the existing mocks: **deterministic** (seed randomness on the symbol/query so the same input always yields the same output), realistic shapes, no network access.

## 4. NoOp provider (key-gated sources only)

Add `NoOp<Domain>Fetcher` in the same module as the concrete provider, returning empty results (pattern: `NoOpEconomicCalendarFetcher` in `providers/economic_calendar.py`). A missing key or disabled flag must never raise — it degrades to no data.

## 5. Settings

In `backend/backend/settings.py`, next to the existing API config (~lines 41–56):
- Key: `<SOURCE>_API_KEY = load_optional_from_file_or_env("<SOURCE>_API_KEY", "").strip()`
- Toggle: `USE_<SOURCE>_API = os.environ.get('USE_<SOURCE>_API', 'true').lower() == 'true'`
- Computed flag: `<SOURCE>_API_ENABLED = bool(<SOURCE>_API_KEY) and USE_<SOURCE>_API` — key present **AND** flag true.

## 6. Factory

Add `get_default_<domain>_fetcher()` to `backend/base/services/__init__.py` and list it in `__all__`. Copy the structure of `get_default_economic_calendar_fetcher` in that file:
- All imports lazy, inside the function (`django.conf.settings` and providers).
- Branch order: `USE_MOCK_DATA_FETCHER` → return mock; `<SOURCE>_API_ENABLED` false → return NoOp; else → concrete provider with `api_key=settings.<SOURCE>_API_KEY`.

## 7. .env.example

Add `#<SOURCE>_API_KEY=...` and `#USE_<SOURCE>_API=true` to the commented "Optional" block in `.env.example`, with the same comment style as the existing entries.

## 8. Tests

Create `backend/base/tests/test_<domain>_fetcher.py`, modeled on `backend/base/tests/test_mock_news_calendar.py`:
- Mock determinism: same query → identical result; different queries → different results.
- Result shape: required keys/columns present, dates/numbers parse.
- Factory wiring via `override_settings`: mock flag on → `Mock*` instance; `*_API_ENABLED` false → `NoOp*` instance; enabled with a dummy key → concrete class (do not call the network in the enabled test — assert the type only).

## 9. Guardrails

- Never import a concrete provider from a view, service, selector, or management command — only the factory.
- Consuming services accept the fetcher as a parameter defaulting to the factory result, e.g. `def get_x(..., fetcher=None): fetcher = fetcher or get_default_<domain>_fetcher()`, so tests can inject a fake.

## 10. Verify

From `backend/`:

```
DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test base --no-input
```

All tests must pass. On Windows/PowerShell: `$env:DJANGO_SETTINGS_MODULE = 'backend.settings_test'; python manage.py test base --no-input`.
