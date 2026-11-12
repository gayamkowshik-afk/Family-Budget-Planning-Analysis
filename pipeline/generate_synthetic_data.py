"""Recruiter note: real family bank data is private, so I generate realistic fake data (salary, rent,
groceries, festival-season shopping, one deliberate outlier). Labels are known, so I can measure my
models honestly. Prices include seasonality (onion spikes) and differences between stores."""
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from common import RAW

random.seed(42)
rng = np.random.default_rng(42)
PEOPLE = ["Ravi Kumar", "Anita S", "Mohit", "Priya N", "Sameer", "Kavya", "Arjun R"]
# (description template, category, min, max, times per month)
TEMPLATES = [
    ("UPI/DMART RICE 10KG/{n}", "Groceries", 600, 680, 1), ("UPI/KIRANA TOOR DAL 2KG/{n}", "Groceries", 300, 360, 1),
    ("UPI/FORTUNE OIL 5L/{n}", "Groceries", 650, 780, 0.7), ("BIGBASKET GROCERY ORDER {n}", "Groceries", 1500, 3500, 2),
    ("UPI/SABZI MANDI ONION TOMATO/{n}", "Vegetables", 200, 450, 4), ("SWIGGY*ORD{n}", "Dining", 250, 900, 5),
    ("ZOMATO ORDER {n}", "Dining", 250, 800, 3), ("UBER TRIP {n}", "Transport", 150, 450, 4),
    ("HP PETROL PUMP {n}", "Transport", 1200, 2000, 2), ("MSEB ELECTRICITY BILL {n}", "Utilities", 1200, 2400, 1),
    ("JIO RECHARGE {n}", "Utilities", 999, 999, 1), ("INDANE GAS CYLINDER {n}", "Utilities", 910, 930, 0.7),
    ("NETFLIX.COM {n}", "Entertainment", 649, 649, 1), ("SPOTIFY INDIA {n}", "Entertainment", 119, 119, 1),
    ("AMZN PAY INDIA {n}", "Shopping", 300, 3500, 2), ("FLIPKART ORDER {n}", "Shopping", 400, 3000, 1),
    ("APOLLO PHARMACY {n}", "Health", 200, 1200, 1), ("UPI/HOUSE RENT/{n}", "Rent", 18000, 18000, 1),
    ("POS SHARMA PROVISIONS {n}", "Groceries", 300, 1800, 1), ("UPI/RELIANCE FRESH/{n}", "Vegetables", 200, 900, 1),
    ("UPI/MEDPLUS {n}", "Health", 150, 900, 0.6), ("UPI/BOOKMYSHOW {n}", "Entertainment", 300, 1200, 0.8),
    ("UPI/RAPIDO RIDE {n}", "Transport", 60, 200, 2), ("UPI/EATFIT MEAL {n}", "Dining", 200, 600, 1.5),
    ("POS CROMA STORES {n}", "Shopping", 800, 6000, 0.5), ("UPI/DECATHLON {n}", "Shopping", 500, 3500, 0.5),
    ("TUITION FEES {n}", "Education", 3000, 3000, 1), ("UPI/{p}/gift", "Others", 200, 2000, 1.5),
]


def transactions(months: int = 12) -> pd.DataFrame:
    rows, start = [], date.today().replace(day=1) - timedelta(days=30 * (months - 1))
    for m in range(months):
        base = (start + timedelta(days=30 * m)).replace(day=1)
        rows.append((base + timedelta(days=1), "SALARY CREDIT ACME LTD", 68000 + random.randint(-500, 500), "Income", ""))
        for tpl, cat, lo, hi, freq in TEMPLATES:
            for _ in range(int(freq) + (random.random() < freq % 1)):
                d = base + timedelta(days=random.randint(0, 27))
                n = random.randint(10000, 99999)
                rows.append((d, tpl.format(n=n, p=random.choice(PEOPLE)), random.randint(lo, hi), cat, f"TXN{n}{m}"))
    # one deliberate outlier so anomaly detection has something to find
    rows.append((date.today() - timedelta(days=20), "AMZN PAY INDIA 55555", 24999, "Shopping", "TXNBIG1"))
    df = pd.DataFrame(rows, columns=["date", "description", "amount", "category", "txn_ref"])
    return df.sort_values("date").reset_index(drop=True)


def prices(days: int = 365) -> pd.DataFrame:
    base = {"rice": 62, "dal": 165, "atta": 42, "oil": 135, "onion": 34, "tomato": 30, "milk": 58}
    stores = {"Local kirana": 1.0, "Supermarket": 0.96, "Online app": 0.93}
    out, idx = [], pd.date_range(end=date.today(), periods=days)
    for product, b in base.items():
        noise = np.zeros(days)
        for i in range(1, days):  # slowly drifting random noise
            noise[i] = 0.9 * noise[i - 1] + rng.normal(0, 0.012)
        doy = idx.dayofyear.values
        season = 0.18 * np.exp(-((doy - 270) ** 2) / 1500) if product in ("onion", "tomato") else 0.03 * np.sin(doy / 58)
        for store, f in stores.items():
            for d, s, nz in zip(idx, season, noise):
                out.append((d.date(), product, store, round(b * f * (1 + s + nz), 2), "synthetic"))
    return pd.DataFrame(out, columns=["date", "product", "store", "price", "source"])


if __name__ == "__main__":
    tx, pr = transactions(), prices()
    tx.to_csv(RAW / "synthetic_transactions.csv", index=False)
    pr.to_csv(RAW / "synthetic_prices.csv", index=False)
    print(f"transactions: {len(tx)} rows | prices: {len(pr)} rows")
