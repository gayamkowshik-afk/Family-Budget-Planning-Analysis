"""Recruiter note: one command runs the whole data pipeline end to end:
generate data -> collect prices -> clean -> train model -> backtest forecasts -> load database.
Run it with:  python pipeline/run_pipeline.py"""
import time

import backtest_forecast
import clean_transactions
import fetch_prices
import generate_synthetic_data as gen
import load_to_db
import train_categorizer
from common import RAW


def step(name, fn):
    t = time.time()
    print(f"\n== {name} ==")
    fn()
    print(f"({time.time() - t:.1f}s)")


def generate():
    gen.transactions().to_csv(RAW / "synthetic_transactions.csv", index=False)
    gen.prices().to_csv(RAW / "synthetic_prices.csv", index=False)


if __name__ == "__main__":
    step("1. Generate raw data", generate)
    step("2. Collect prices", fetch_prices.main)
    step("3. Clean transactions", clean_transactions.main)
    step("4. Train categorizer", train_categorizer.main)
    step("5. Backtest price forecaster", backtest_forecast.main)
    step("6. Load database", load_to_db.main)
    print("\nPipeline finished. Start the API: cd backend && uvicorn app.main:app --reload")
