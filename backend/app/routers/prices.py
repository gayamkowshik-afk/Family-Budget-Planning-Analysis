"""Recruiter note: price intelligence. Combines (1) how often this family buys each item,
(2) recent market prices and (3) a short forecast, then explains whether to buy now, wait or stock up."""
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PricePoint, Transaction, User
from ..schemas import PriceIn
from ..security import current_user
from ..services import forecast, recommender

router = APIRouter(tags=["prices"])


def daily_average(db, product: str, days: int = 120):
    since = date.today() - timedelta(days=days)
    rows = db.query(PricePoint).filter(PricePoint.product == product, PricePoint.date >= since).order_by(PricePoint.date).all()
    by_day = defaultdict(list)
    for r in rows:
        by_day[r.date].append(r.price)
    return [(d, sum(v) / len(v)) for d, v in sorted(by_day.items())]


@router.post("/prices", status_code=201)
def contribute(body: PriceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Crowdsourced price: a user reports what they paid. This is how store-level data grows."""
    db.add(PricePoint(product=body.product.lower(), store=body.store, price=body.price,
                      date=body.date or date.today(), source="crowd"))
    db.commit()
    return {"ok": True}


@router.get("/prices/{product}/trend")
def trend(product: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    series = daily_average(db, product.lower())
    if len(series) < 14:
        raise HTTPException(404, "Not enough price history for this product yet.")
    values = [p for _, p in series]
    return {"product": product, "history": [{"date": str(d), "price": round(p, 2)} for d, p in series[-30:]],
            "forecast_next_7_days": [round(v, 2) for v in forecast.holt_forecast(values)],
            "backtest": forecast.backtest(values)}


@router.get("/recommendations")
def recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter_by(family_id=user.family_id).all()
    out = []
    for product, perishable in recommender.TRACKED.items():
        series = daily_average(db, product)
        if len(series) < 14:
            continue
        values = [p for _, p in series]
        dates = [t.date for t in txs if product in t.description.lower()]
        due = recommender.days_until_due(dates, date.today()) if dates else None
        advice = recommender.advise(values, forecast.holt_forecast(values), due, perishable)
        out.append({"product": product, "price_today": round(values[-1], 2), "next_purchase_in_days": due, **advice})
    return sorted(out, key=lambda x: (x["next_purchase_in_days"] is None, x["next_purchase_in_days"] or 0))


@router.get("/stores/compare")
def compare(products: str = Query(..., description="comma separated, e.g. rice,dal,oil"),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    wanted = [p.strip().lower() for p in products.split(",") if p.strip()]
    totals = defaultdict(float)
    for product in wanted:
        latest = (db.query(PricePoint).filter_by(product=product).order_by(PricePoint.date.desc()).limit(30).all())
        newest = {}
        for r in latest:
            newest.setdefault(r.store, r.price)
        for store, price in newest.items():
            totals[store] += price
    if not totals:
        raise HTTPException(404, "No price data for those products.")
    ranked = sorted(({"store": s, "basket_cost": round(recommender.effective_basket_cost(s, t), 2)} for s, t in totals.items()),
                    key=lambda x: x["basket_cost"])
    return {"products": wanted, "cheapest": ranked[0]["store"], "stores": ranked}
