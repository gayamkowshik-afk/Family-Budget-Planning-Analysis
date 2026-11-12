"""Recruiter note: tests for the buy/wait logic and the forecaster."""
from datetime import date

from app.services import forecast, recommender


def test_purchase_cycle():
    assert recommender.purchase_cycle([date(2026, 1, 1), date(2026, 1, 31), date(2026, 3, 2)]) == 30


def test_wait_when_price_falling():
    hist = [60, 62, 64, 66, 68, 70]
    assert recommender.advise(hist, [60, 59, 58])["action"] == "wait"


def test_stock_up_when_cheap_and_storable():
    hist = [70, 68, 66, 64, 62, 60]
    assert recommender.advise(hist, [60, 60, 60], perishable=False)["action"] == "stock_up"


def test_online_delivery_fee_applies_below_threshold():
    assert recommender.effective_basket_cost("Online app", 300) == 340
    assert recommender.effective_basket_cost("Online app", 800) == 800


def test_holt_follows_a_rising_trend():
    assert forecast.holt_forecast([10, 11, 12, 13, 14, 15], 3)[-1] > 15
