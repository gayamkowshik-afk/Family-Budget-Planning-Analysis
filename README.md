# FamilyFinance Pro

A full-stack family budget platform: it cleans messy bank statements, categorizes spending with ML,
spots unusual spends, advises **what to buy, when, and where**, and includes a consent-based
**money wallet for children**.

> **For recruiters (30-second version):** I built the whole data journey a data analyst owns:
> messy raw data -> cleaning -> model -> forecast -> API -> decision a family can act on.
> Every file starts with a plain-English "Recruiter note" saying what it does and why.

## What it does

| Feature | Where to look |
|---|---|
| Add spends manually, upload bank CSV, verify a payment (ID + OTP, mock gateway) | `backend/app/routers/transactions.py` |
| Data cleaning: date/amount formats, merchant names, duplicates | `backend/app/services/cleaning.py` |
| Auto-categorization: rules + ML with confidence scores | `backend/app/services/categorizer.py`, `pipeline/train_categorizer.py` |
| Savings rate, 50/30/20 check, anomalies, recurring bills, health score | `backend/app/services/insights.py` |
| Buy now / wait / stock up, with a plain-English reason | `backend/app/services/recommender.py` |
| 7-day price forecast and honest backtest | `backend/app/services/forecast.py`, `pipeline/backtest_forecast.py` |
| Offline vs online basket comparison (delivery fees included) | `backend/app/routers/prices.py` |
| Child wallet: allowance, limits, goals, coaching (no secret tracking) | `backend/app/routers/children.py` |
| Login, hashed passwords, JWT, per-family data isolation | `backend/app/security.py` |

## Architecture

```
 Browser (frontend/index.html)
        | HTTPS + JWT
 FastAPI backend ---- routers (auth, transactions, analytics, prices, children)
        |                 |
        |            services (cleaning, categorizer, insights, forecast, recommender)
        |
 PostgreSQL (SQLite for quick local runs)
        ^
 Data pipeline (pipeline/run_pipeline.py)
   generate data -> collect prices -> clean -> train model -> backtest -> load DB
```

## Run it

**Option A: Python (fastest)**
```bash
pip install -r backend/requirements.txt
python pipeline/run_pipeline.py              # builds data, trains model, loads demo family
cd backend && uvicorn app.main:app --reload  # API docs at http://localhost:8000/docs
```
Open `frontend/index.html` in a browser. Demo login: `demo@familyfinance.dev` / `demo1234`.
Try uploading `data/sample_statement.csv`. Demo OTP for verification is `123456`.

**Option B: Docker (API + PostgreSQL + website)**
```bash
docker compose up --build
# API http://localhost:8000/docs   |  website http://localhost:8080
# then load demo data: DATABASE_URL=postgresql://ffp:ffp@localhost:5432/ffp python pipeline/run_pipeline.py
```
(Add `ports: ["5432:5432"]` to the `db` service if you want to run the pipeline from your machine.)

**Tests:** `cd backend && pytest -q` (13 tests, also run on every push by GitHub Actions).

## Results (from the included pipeline run)

| Check | Result |
|---|---|
| Categorization on held-out rows, keyword rules only | 85.3% |
| Categorization, rules + ML hybrid (what the app uses) | 100% on synthetic data |
| 7-day price forecast vs "price stays the same" guess | Roughly tied (about 1.8% average error for both) |

Please read these honestly:
- The 100% is on **synthetic** transactions, so it proves the pipeline works, not real-world accuracy. The meaningful number is the jump from 85% to 100% on merchants the rules had never seen. Next step: label 500 real statement rows and re-test.
- The forecaster does **not** clearly beat the naive guess on smooth prices. I kept it because it ties, it is cheap, and the recommender only acts on forecasts that move more than 3%. Real mandi data with sharper swings (onion, tomato) is where it should earn its place.

## Decisions I made on purpose

- **Mock payment gateway.** A transaction ID alone cannot pull history from a bank, and India's Account Aggregator network needs an RBI-regulated licence. The mock shows the flow behind one function so a real provider can replace it.
- **No scraping of shopping sites.** It breaks their terms and fails often. Price sources are government mandi data (data.gov.in, set `DATA_GOV_API_KEY`), crowdsourced prices (`POST /prices`) and synthetic data for training.
- **Child wallet is transparent.** Parent consent *and* the child's agreement are required, and the child sees what the parent sees. This follows the spirit of India's DPDP Act 2023 on children's data.
- **Security basics:** salted password hashing, signed tokens, data scoped by `family_id`, secrets from environment variables.

## Known limits and next steps

- Demo data and prices are synthetic. Real bills (OCR) would give store-level prices.
- Tighten CORS and use a proper secret before any real deployment; add database migrations (Alembic).
- Next: receipt OCR, SMS parsing, Account Aggregator sandbox, Prophet/SARIMA for seasonal items, a redesigned front end.

*Educational project. Insights are informational, not financial advice.*
