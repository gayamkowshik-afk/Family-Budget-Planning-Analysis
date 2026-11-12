"""Recruiter note: price collection. If a free data.gov.in key is set, it pulls real government
mandi (wholesale market) prices. If not, or if the service is down, it falls back to the synthetic
prices so the pipeline never breaks. I do not scrape shopping sites because it breaks their terms."""
import os
import shutil

import pandas as pd
import requests

from common import PROCESSED, RAW

# Agmarknet "current daily price of commodities" dataset on data.gov.in (check the id on the portal if it changes)
URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
WANTED = {"onion": "onion", "tomato": "tomato", "rice": "rice"}


def fetch_govt(key: str) -> pd.DataFrame:
    rows = []
    for name in WANTED:
        r = requests.get(URL, params={"api-key": key, "format": "json", "limit": 100, "filters[commodity]": name.title()}, timeout=15)
        r.raise_for_status()
        for rec in r.json().get("records", []):
            rows.append((pd.to_datetime(rec["arrival_date"], dayfirst=True).date(), name, "Govt mandi",
                         float(rec["modal_price"]) / 100, "govt"))  # quintal price -> per kg
    return pd.DataFrame(rows, columns=["date", "product", "store", "price", "source"])


def main():
    out = PROCESSED / "prices.csv"
    key = os.getenv("DATA_GOV_API_KEY")
    synthetic = pd.read_csv(RAW / "synthetic_prices.csv")
    if key:
        try:
            govt = fetch_govt(key)
            pd.concat([synthetic, govt]).to_csv(out, index=False)
            print(f"prices: {len(govt)} real mandi rows added to synthetic base")
            return
        except Exception as e:
            print("government API failed, using synthetic prices:", e)
    shutil.copy(RAW / "synthetic_prices.csv", out)
    print("prices: using synthetic data (set DATA_GOV_API_KEY for real mandi prices)")


if __name__ == "__main__":
    main()
