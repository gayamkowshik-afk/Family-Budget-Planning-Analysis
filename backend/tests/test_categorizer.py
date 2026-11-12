"""Recruiter note: tests that the rule layer gets common merchants right."""
from app.services.categorizer import categorize


def test_rules():
    assert categorize("SWIGGY*ORD123")[0] == "Dining"
    assert categorize("MSEB ELECTRICITY BILL")[0] == "Utilities"
    assert categorize("SALARY CREDIT")[0] == "Income"
