# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Captrivio — a portfolio-tracking app for retail investors. Django REST backend + React/Vite SPA, PostgreSQL, deployed via Docker. Backend lives in `backend/`, frontend in `frontend/`, compose/stack files in `docker/`.

## Commands

### Backend (run from `backend/`)
- **Tests:** `DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test --no-input` — uses in-memory SQLite, no PostgreSQL needed. CI runs exactly this.
- **Single test:** `DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test portfolio.tests.test_calculators` (append `.ClassName.test_method` to narrow further).
- **Migrations:** `python manage.py makemigrations` / `python manage.py migrate`.
- **Dev server:** `python manage.py runserver` (requires the env vars in `.env.example`; `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `POSTGRES_*` have **no defaults** and must be set, or use `settings_test`).
- Dependencies: `requirements.txt` (full, includes ML), `requirements-docker.txt` (slim, used by CI and prod image).

### Frontend (run from `frontend/`)
- **Tests:** `npm run test` (Vitest, jsdom). Watch mode: `npm run test:watch`.
- **Lint:** `npm run lint` (ESLint, `--max-warnings 0`).
- **Dev:** `npm run dev` (Vite, port 5173; proxies `/api` to `VITE_PROXY_TARGET` or `http://127.0.0.1:8000`).
- **Build:** `npm run build`.

### Docker
- **Demo (no config/keys, mock data, pre-built GHCR images):** `docker compose -f docker/docker-compose.demo.yml --project-directory . up -d` → http://localhost:80
- **Dev (build locally):** `docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --project-directory . up --build` → frontend :5173, API :8000, pgAdmin :5050

## Architecture

### Backend layering (per Django app)
Three apps — `base`, `portfolio`, `analytics` — each follow the same layered structure. **Dependencies point inward:** views → services/selectors → interfaces/models. Keep this direction when adding code.

- `views/` (or `views.py`) — thin HTTP handlers; delegate to services/selectors, do not put business logic here.
- `services/` — business logic / use cases (write side, metric computation).
- `selectors/` — read-only queries and data assembly, no side effects.
- `serializers.py` — DRF (de)serialization and validation.
- `infrastructure/` — `interfaces/` (abstract base classes) + `db/` (repositories) + `providers/` (concrete external-data implementations). Domain code depends on the interfaces, never on a concrete provider.
- `management/commands/` — seed commands and batch jobs (reuse services, don't duplicate logic).

App responsibilities: `base` = users/auth (JWT), assets & search, market data, news, calendar, bonds; `portfolio` = transactions, composition/allocation, value history, risk metrics (Sharpe/Sortino/Alpha); `analytics` = forecasts and optional ML (persisted models in `analytics/saved_models/`).

### Data-fetcher dependency injection (important)
External data is accessed through interfaces, never instantiated directly in views/services. The factory functions in `backend/base/services/__init__.py` (`get_default_stock_fetcher`, `get_default_crypto_fetcher`, `get_default_fx_fetcher`, `get_default_news_fetchers`, `get_default_economic_calendar_fetcher`) choose the implementation based on settings flags:

- `USE_MOCK_DATA_FETCHER=true` → returns `Mock*` fetchers (deterministic, symbol-seeded data, no network) instead of the `yfinance_fetchers`. Use this for local dev/tests without API keys.
- News and economic-calendar providers are gated by `*_API_ENABLED` flags (key present **AND** the corresponding `USE_*_API` flag true). When disabled, a `NoOp*` fetcher is returned rather than raising.

When adding a new external data source: define an interface in `base/infrastructure/interfaces/`, add a concrete provider in `base/infrastructure/providers/`, and wire selection through a factory in `base/services/__init__.py` — don't import a concrete provider from a view or service.

### Settings & feature flags
- `backend/backend/settings.py` reads everything from env (`secrets_util.load_from_file_or_env` also supports `*_FILE` paths for Docker Swarm secrets).
- `backend/backend/settings_test.py` sets test env defaults and forces in-memory SQLite — always use it for tests.
- `ENABLE_ML_FUNCTIONS=false` (default) disables TensorFlow/Keras + Transformers (sentiment, LSTM forecasts become no-ops). Don't assume ML deps are importable unless this is true.

### Frontend
React Router SPA. `App.jsx` defines routes and wraps the app in `AuthContext` (JWT access+refresh handling). API calls go through `src/api/client.js`; pages in `src/pages/`, reusable UI in `src/components/`. Talks to the backend over REST with JWT bearer tokens.

## CI / deployment
- PRs to `main` run `.github/workflows/tests.yml` (backend + frontend tests). Match those commands locally before pushing.
- Push to `main` runs `.github/workflows/pipeline.yml`: tests → build & push backend/frontend images to GHCR → `docker stack deploy` over SSH (`docker/docker-stack.prod.yaml`). The frontend `:demo` image is built with `VITE_USE_MOCK_DATA_FETCHER=true`.
