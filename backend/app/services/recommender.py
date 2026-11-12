"""Recruiter note: the "what to buy and when, and where" brain. It is deliberately rule-based and
explainable: every recommendation comes with a plain-English reason, which is what a real user
(and an interviewer) wants to see."""
from datetime import date
from statistics import mean

# False = can be stored for weeks, True = spoils quickly so "stock up" is a bad idea.
TRACKED = {"rice": False, "dal": False, "atta": False, "oil": False, "onion": True, "tomato": True, "milk": True}
STORE_RULES = {"Online app": {"delivery_fee": 40, "free_above": 499}}  # offline stores have no fee but cost a trip


def purchase_cycle(dates: list[date]):
    """Average gap in days between purchases of an item, or None if we have fewer than 2."""
    d = sorted(dates)
    gaps = [(b - a).days for a, b in zip(d, d[1:]) if (b - a).days > 0]
    return round(mean(gaps)) if gaps else None


def days_until_due(dates: list[date], today: date):
    cycle = purchase_cycle(dates)
    if cycle is None:
        return None
    return cycle - (today - max(dates)).days


def advise(history: list[float], forecast: list[float], due_in=None, perishable=False) -> dict:
    cur = history[-1]
    rank = sum(1 for h in history if h <= cur) / len(history)  # 0 = cheapest ever seen, 1 = priciest
    fut = mean(forecast) if forecast else cur
    if fut < cur * 0.97 and (due_in is None or due_in > 2):
        return {"action": "wait", "reason": f"Prices are expected to fall about {round((1 - fut / cur) * 100)}% this week."}
    if rank <= 0.2 and not perishable:
        return {"action": "stock_up", "reason": "Price is in its lowest 20% for the period and the item keeps well."}
    if rank <= 0.35 or fut > cur * 1.03:
        why = "Price is low compared with recent history." if rank <= 0.35 else "Prices are expected to rise."
        return {"action": "buy_now", "reason": why}
    return {"action": "fair_price", "reason": "Price is in the normal range. Buy when you actually need it."}


def effective_basket_cost(store: str, items_total: float) -> float:
    rule = STORE_RULES.get(store)
    if rule and items_total < rule["free_above"]:
        return items_total + rule["delivery_fee"]
    return items_total
