"""Recruiter note: a small price forecaster (damped-trend Holt, written by hand so it has no heavy
dependencies) plus a backtest that checks it against the naive "price stays the same" guess.
Honest finding: on smooth, mean-reverting prices the naive guess is very hard to beat, so the
recommender only acts on a forecast when it moves more than 3%."""
from statistics import mean


def holt_forecast(y, steps: int = 7, alpha: float = 0.8, beta: float = 0.05, phi: float = 0.8):
    """phi < 1 'damps' the trend so it fades out instead of running away."""
    level, trend = y[0], (y[1] - y[0] if len(y) > 1 else 0.0)
    for v in y[1:]:
        prev = level
        level = alpha * v + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - prev) + (1 - beta) * phi * trend
    out, cum = [], 0.0
    for i in range(1, steps + 1):
        cum += phi ** i
        out.append(level + cum * trend)
    return out


def mape(actual, predicted) -> float:
    return mean(abs(a - p) / a for a, p in zip(actual, predicted)) * 100


def backtest(y, horizon: int = 7, start: int = 60, step: int = 7) -> dict:
    """Walk forward through history: forecast the next week, compare to what really happened."""
    naive, holt = [], []
    for i in range(start, len(y) - horizon, step):
        actual = y[i:i + horizon]
        naive.append(mape(actual, [y[i - 1]] * horizon))
        holt.append(mape(actual, holt_forecast(y[:i], horizon)))
    return {"naive_mape": round(mean(naive), 2), "holt_mape": round(mean(holt), 2), "windows": len(naive)}
