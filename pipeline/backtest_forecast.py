"""Recruiter note: tests the price forecaster the way it will be used: walk through history, predict
the next 7 days, compare with what really happened. The key number is MAPE (average % error), shown
next to the naive "price stays the same" guess. If the model cannot beat naive, I do not ship it."""
import pandas as pd

from common import PROCESSED, REPORTS
from app.services.forecast import backtest


def main():
    df = pd.read_csv(PROCESSED / "prices.csv", parse_dates=["date"])
    rows = []
    for product, g in df.groupby("product"):
        series = g.groupby("date")["price"].mean().sort_index().tolist()
        if len(series) > 80:
            rows.append({"product": product, **backtest(series)})
    out = pd.DataFrame(rows)
    out["holt_beats_naive"] = out["holt_mape"] < out["naive_mape"]
    out.to_csv(REPORTS / "forecast_metrics.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
