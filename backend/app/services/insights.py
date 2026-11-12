"""Recruiter note: the analytics. Monthly totals, savings rate, unusual-spend detection (z-score),
recurring-payment detection and a simple 0-100 household health score."""
from collections import defaultdict
from statistics import mean, pstdev

NEEDS = {"Groceries", "Vegetables", "Utilities", "Rent", "Education", "Health", "Transport"}


def monthly_summary(txs, month: str) -> dict:
    rows = [t for t in txs if t.date.strftime("%Y-%m") == month]
    income = sum(t.amount for t in rows if t.category == "Income")
    by_cat = defaultdict(float)
    for t in rows:
        if t.category != "Income":
            by_cat[t.category] += t.amount
    spent = sum(by_cat.values())
    needs = sum(v for c, v in by_cat.items() if c in NEEDS)
    return {"month": month, "income": round(income, 2), "spent": round(spent, 2),
            "savings_rate_pct": round((income - spent) / income * 100, 1) if income else None,
            "needs_pct_of_spend": round(needs / spent * 100, 1) if spent else None,  # 50/30/20 check
            "by_category": {k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda x: -x[1])}}


def find_anomalies(txs, z_limit: float = 2.5, min_rows: int = 6):
    """A spend is 'unusual' if it is far above that category's normal range."""
    groups = defaultdict(list)
    for t in txs:
        if t.category != "Income":
            groups[t.category].append(t)
    out = []
    for cat, rows in groups.items():
        if len(rows) < min_rows:
            continue
        m, sd = mean(r.amount for r in rows), pstdev(r.amount for r in rows)
        if sd == 0:
            continue
        out += [{"id": r.id, "date": str(r.date), "description": r.description, "amount": r.amount,
                 "category": cat, "z_score": round((r.amount - m) / sd, 1)}
                for r in rows if (r.amount - m) / sd > z_limit]
    return sorted(out, key=lambda x: -x["z_score"])


def find_recurring(txs):
    """Same merchant, in 3+ different months, with a stable amount: rent, EMIs, subscriptions."""
    groups = defaultdict(list)
    for t in txs:
        if t.category != "Income":
            groups[t.merchant or t.description].append(t)
    out = []
    for name, rows in groups.items():
        months = {r.date.strftime("%Y-%m") for r in rows}
        amounts = [r.amount for r in rows]
        if len(months) >= 3 and max(amounts) <= 1.15 * min(amounts):
            out.append({"merchant": name, "typical_amount": round(mean(amounts), 2), "months_seen": len(months)})
    return sorted(out, key=lambda x: -x["typical_amount"])


def health_score(summary: dict, budgets: dict) -> dict:
    """40 pts savings rate (30%+ is full marks) + 40 pts budget discipline + 20 pts needs/wants balance."""
    rate = (summary["savings_rate_pct"] or 0) / 100
    s1 = max(0, min(rate, 0.3)) / 0.3 * 40
    over = [c for c, lim in budgets.items() if summary["by_category"].get(c, 0) > lim]
    s2 = (1 - len(over) / len(budgets)) * 40 if budgets else 20
    needs = summary["needs_pct_of_spend"]
    s3 = 20 if needs is not None and needs <= 60 else 10
    return {"score": round(s1 + s2 + s3), "over_budget": over}
