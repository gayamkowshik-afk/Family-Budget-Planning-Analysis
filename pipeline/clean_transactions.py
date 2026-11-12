"""Recruiter note: raw -> clean. Normalises merchant names, removes duplicates and bad rows, and
writes a tidy file that the model and database steps use. It reuses the same cleaning code as the API,
so the batch pipeline and the live app can never disagree."""
import pandas as pd

from common import PROCESSED, RAW
from app.services.cleaning import normalize_merchant


def main():
    df = pd.read_csv(RAW / "synthetic_transactions.csv")
    before = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "description"]).query("amount > 0")
    df["merchant"] = df["description"].map(normalize_merchant)
    df = df.drop_duplicates(subset=["date", "description", "amount"])
    df.to_csv(PROCESSED / "transactions.csv", index=False)
    print(f"transactions: {before} raw -> {len(df)} clean rows")


if __name__ == "__main__":
    main()
