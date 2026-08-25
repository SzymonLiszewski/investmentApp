# Captrivio

Captrivio is an application for retail investors whose **main focus is portfolio tracking**. Add positions (stocks, bonds, ETFs), view portfolio composition and allocation by asset class, track returns over time, and monitor risk metrics and performance in your chosen currency. The app also provides access to quotes, technical and fundamental indicators, simple price forecasts, and financial news with sentiment analysis - all in one place.

**Main features:**

- **Portfolio** - record transactions, view composition and allocation, value history, risk indicators (Sharpe, Sortino) and Alpha.
- **Quotes and market data** - stock and index prices, fundamental data (P/E, dividend) and technical indicators (RSI, moving averages).
- **Forecasts** - simple price forecasts based on historical trends.
- **News and sentiment** - financial news with sentiment scoring (optional, use ENABLE_ML_FUNCTIONS=true).
- **Calendar** - earnings report dates and IPO calendar.

**Live demo:** A live demo is available at https://captrivio.com (this demo uses mock data for illustrative purposes only)

---

## Running the app

### Docker - demo (no config, no API keys)

Runs the same stack as production using **pre-built images from GHCR**, with all required environment variables set and **mock data fetcher** enabled - no `.env` or API keys needed. Useful for a quick try-out or demos. For real data, disable the mock fetcher and set the relevant provider options, provide API keys where required - see .env.example for examples

```bash
docker compose -f docker/docker-compose.demo.yml --project-directory . up -d
```

- **App:** http://localhost:80 (Caddy proxies to frontend and backend).
- Database is seeded with sample assets (stocks, crypto, bonds, economic data) and stored in volume `postgres_data_demo`.
- Stock/crypto quotes and similar data come from the mock fetcher (deterministic test data), not live APIs.
- No Redis/Celery here on purpose, to keep the demo zero-config - the forecast endpoints just fit a model on demand instead of using a nightly-trained one.


### Quick start (Docker)

From the repository root:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --project-directory . up --build
```

- **App:** http://localhost:5173  
- **API:** http://localhost:8000  
- **pgAdmin:** http://localhost:5050 (login: `admin@stocksense.local` / `admin`; add server: host `db`, user `stocksense`, password `stocksense`, database `stocksense`).

Database and seed data are stored in volume `postgres_data_dev`.

Also starts `redis` + `celery-worker` + `celery-beat` for background jobs - nightly retraining of the SARIMA/regression forecast models (schedule in `CELERY_BEAT_SCHEDULE`, `backend/backend/settings.py`). Trained model artifacts land in volume `ml_models`. Without these, forecast endpoints still work, just by fitting a model on demand instead of using a nightly-trained one.


### Running without Docker

1. Clone the repository and enter the directory:
   ```bash
   git clone https://github.com/SzymonLiszewski/investmentApp
   cd investmentApp
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. (Optional) Mock mode - no API keys:
   - Set `USE_MOCK_DATA_FETCHER=true` in your environment or `.env`. Fetchers will return deterministic test data.

4. API keys - needed only if you use the live APIs for **news** and **economic calendar** (see `.env.example`). Copy `.env.example` to `.env` and set:
   - **ALPHAVANTAGE_API_KEY** - for stock prices and economic calendar (earnings, IPO dates).
   - **NEWSDATA_API_KEY** - for NewsData-based news fetching.
   - With `USE_MOCK_DATA_FETCHER=true`, stock/crypto/FX use mock data and do not need these; news and calendar still call the real APIs when used, so set the keys if you want those features to work.
   - **Linux:** `export ALPHAVANTAGE_API_KEY=... NEWSDATA_API_KEY=...`
   - **Windows:** `set ALPHAVANTAGE_API_KEY=...` and `set NEWSDATA_API_KEY=...`

5. Run the backend (SQLite by default; set `POSTGRES_*` env vars for PostgreSQL):
   ```bash
   cd backend
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

6. (Optional) Background jobs - nightly retraining of the forecast models runs via Celery; skip this and forecast endpoints just fit a model on demand instead. Needs Redis running locally, then in two more terminals:
   ```bash
   celery -A backend worker -l info
   celery -A backend beat -l info
   ```

7. In another terminal - frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

8. Open in browser: http://localhost:5173

### Production (Docker Swarm + CI/CD)

The hosted demo (https://captrivio.com) runs on `docker/docker-stack.prod.yaml`, a Docker Swarm stack: `db`, `backend`, `redis` + `celery-worker` + `celery-beat` (nightly forecast-model retraining), `frontend`, `caddy` (reverse proxy, automatic HTTPS), plus the monitoring services below. Secrets (DB password, Django secret key, API keys, Grafana admin password) are Swarm secrets rather than plain env vars.

**CI/CD** (`.github/workflows/pipeline.yml`): every push to `main` runs the backend/frontend test suites, builds and pushes the backend/frontend images to GHCR, then deploys the stack via `docker stack deploy` over SSH - so the live demo always reflects `main`.

### Monitoring

The same stack includes **Prometheus** + **Grafana** for basic metrics:

- **App metrics** - request counts/latency and DB query stats, exposed by the backend at `/metrics` (via `django-prometheus`) and scraped internally by Prometheus.
- **Host/container metrics** - `node-exporter` (host CPU/memory/disk) and `cAdvisor` (per-container resource usage).
- **Access is intentionally private** - no dashboard is exposed publicly. Reach Grafana over an SSH tunnel to the host:
  ```bash
  ssh -L 3000:localhost:3000 <user>@<host>
  ```
  then open http://localhost:3000 and log in with the `grafana_admin_password` secret. Prometheus, node-exporter, and cAdvisor have no published port at all - they're reachable only over the internal Docker network.

---

## Application architecture

### Overview

- **Frontend (React)** - SPA talking to the Django API over REST; JWT authentication (token + refresh).
- **Backend (Django)** - REST API split into apps: `base`, `portfolio`, `analytics`.
- **Database** -  PostgreSQL
- **Background jobs (Celery)** - nightly retraining of the SARIMA/regression forecast models, Redis as the broker (optional - see "Running the app" above).
- **External APIs** - Alpha Vantage, Yahoo Finance, newsdata.

### Backend apps (`base` / `portfolio` / `analytics`)

**App responsibilities:**

- **`base`** - Users, registration, JWT; assets (stocks/indices) and search; market data (quotes, fundamental, technical); news; calendar (earnings, IPO); bonds (series, macro).
- **`portfolio`** - Transactions, composition, allocation, value history, risk indicators (Sharpe, Sortino) and Alpha, transaction updates.
- **`analytics`** - Advanced analytics (e.g. forecasts, optional ML); may use `saved_models/` for persisted models.



**Each Django app follows a similar layout:**

| Layer | Role |
|-------|------|
| **`models.py`** | Domain models and DB schema. |
| **`views/`** or **`views.py`** | HTTP handlers; expose REST endpoints (thin layer, delegate to services/selectors). |
| **`serializers.py`** | DRF serializers for request/response (validation, (de)serialization). |
| **`urls.py`** | URL routing to views. |
| **`services/`** | Business logic and use cases (e.g. portfolio metrics). |
| **`selectors/`** | Read-only queries and data assembly (no side effects). |
| **`infrastructure/`** | DB access, interfaces, external data providers. |
| **`admin.py`** | Django admin registration. |
| **`management/`** | Custom management commands. |
| **`tests/`** | Unit and integration tests. |

**Main points of the structure**

**Thin views**  
Views are lightweight and delegate logic to services and selectors. This means:

- business and read logic live in one place,
- the same logic can be reused from commands or other entry points.

**Infrastructure behind interfaces**  
Implementations (e.g., mocks or alternative providers) can be swapped without touching the domain.

**Inward-facing dependencies**  
Views depend on services and selectors, which depend on abstractions for external data fetching and on models. This keeps the core stable even if:

- the delivery layer changes (REST API, CLI), or
- external APIs evolve.

It also makes the backend easier to test and extend.


### Frontend structure (`frontend/src/`)

| Path | Role |
|------|------|
| **`main.jsx`**, **`App.jsx`** | Entry point and root: router setup, `AuthProvider`, layout. |
| **`AuthContext.jsx`** | Auth state and token handling (login, logout, refresh). |
| **`api/`** | API client (HTTP, base URL, auth headers). |
| **`pages/`** | Route-level screens: `HomePage`, `Portfolio`, `Analysis`, `Analysis2`, `NewsPage`, `LoginPage`, `RegisterPage`, `AboutPage`, etc. |
| **`components/`** | Reusable UI: `navbar`, `portfolio/` (positions, allocation, add stocks, connect accounts), `login/` (forms), `sentiment/` (news), charts, `styles/` (CSS). |
| **`assets/`** | Static assets (images, etc.). |

Routing is defined in `App.jsx` (React Router); pages fetch data via the `api` client and render components.

---

## Tech stack

| Layer           | Technology |
|-----------------|------------|
| **Backend**     | Python, Django, Django REST Framework |
| **Auth**        | JWT (Simple JWT) |
| **Frontend**    | React, Vite |
| **Database**    | PostgreSQL |
| **External data** | Alpha Vantage, newsdata, marketstack |
| **Background jobs** | Celery, Redis |
| **Deploy**      | Docker, Docker Compose, Caddy, Gunicorn |
| **Monitoring**  | Prometheus, Grafana, cAdvisor, node-exporter |

**Requirements:** Python 3.8+, Node.js and npm for the frontend; optionally API keys (or `USE_MOCK_DATA_FETCHER=true`).

---

## Contributing

Contributions are welcome: ideas, fixes, new features. Open an issue or submit a pull request.

## License

This project is available under the MIT License. See the [LICENSE](LICENSE) file for details.
