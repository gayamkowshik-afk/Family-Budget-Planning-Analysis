"""Recruiter note: tests for the cleaning logic, using the kind of messy input real statements have."""
from datetime import date

from app.services.cleaning import normalize_merchant, parse_amount, parse_date, parse_statement


def test_amount_formats():
    assert parse_amount("₹1,250.50") == 1250.5
    assert parse_amount("(300)") == 300.0


def test_date_formats():
    assert parse_date("05/03/2026") == date(2026, 3, 5)
    assert parse_date("2026-03-05") == date(2026, 3, 5)


def test_merchant_names():
    assert normalize_merchant("SWIGGY*ORD8832 BANGALORE") == "Swiggy"
    assert normalize_merchant("AMZN PAY INDIA 123") == "Amazon"


def test_statement_with_credit_column_and_bad_row():
    csv_text = "Date,Narration,Debit,Credit,Ref No\n05/03/2026,SALARY ACME,,50000,R1\nbad,row,1,,\n06/03/2026,SWIGGY ORDER,450,,R2\n"
    rows = parse_statement(csv_text)
    assert len(rows) == 2 and rows[0]["is_income"] and rows[1]["amount"] == 450
