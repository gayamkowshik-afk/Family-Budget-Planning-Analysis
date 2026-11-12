"""Recruiter note: this is the data-cleaning layer. Real bank statements are messy: odd date
formats, rupee symbols, merchant names full of reference numbers, and duplicate rows. This file
turns all of that into clean, consistent records."""
import csv
import io
import re
from datetime import date, datetime

ALIASES = {"swiggy": "Swiggy", "zomato": "Zomato", "amzn": "Amazon", "amazon": "Amazon", "dmart": "DMart",
           "uber": "Uber", "netflix": "Netflix", "spotify": "Spotify", "jio": "Jio", "bigbasket": "BigBasket",
           "blinkit": "Blinkit", "flipkart": "Flipkart", "apollo": "Apollo Pharmacy", "indane": "Indane Gas",
           "bescom": "Electricity Board", "mseb": "Electricity Board"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d/%m/%y", "%d-%b-%Y")
HEADERS = {"date": ("date", "txn date", "transaction date", "value date"),
           "description": ("description", "narration", "particulars", "details", "remarks"),
           "amount": ("amount", "debit", "withdrawal", "withdrawals", "dr"),
           "credit": ("credit", "deposit", "deposits", "cr"),
           "txn_ref": ("txn_ref", "reference", "ref", "txn id", "transaction id", "utr", "ref no")}


def parse_date(text: str) -> date:
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date: {text!r}")


def parse_amount(text) -> float:
    """'₹1,250.50' -> 1250.5, '(300)' -> 300.0 (brackets mean debit in some statements)."""
    s = re.sub(r"[₹,\sA-Za-z]", "", str(text or ""))
    s = s.strip("()")
    return abs(float(s)) if s not in ("", "-") else 0.0


def normalize_merchant(description: str) -> str:
    low = description.lower()
    for key, name in ALIASES.items():
        if key in low:
            return name
    words = [w for w in re.sub(r"[^a-zA-Z ]", " ", description).split() if w.lower() not in ("upi", "pos", "neft", "imps")]
    return " ".join(words[:2]).title() or "Unknown"


def dedupe_key(d: date, description: str, amount: float):
    return (d, description.strip().lower(), round(amount, 2))


def _pick(row: dict, field: str):
    for h in HEADERS[field]:
        if h in row and str(row[h]).strip():
            return row[h]
    return ""


def parse_statement(text: str) -> list[dict]:
    """Reads a bank/UPI CSV with flexible column names. Rows that cannot be read are skipped."""
    reader = csv.DictReader(io.StringIO(text))
    reader.fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
    rows = []
    for raw in reader:
        row = {k: (v or "").strip() for k, v in raw.items() if k}
        try:
            d = parse_date(_pick(row, "date"))
            desc = _pick(row, "description")
            debit, credit = parse_amount(_pick(row, "amount")), parse_amount(_pick(row, "credit"))
        except ValueError:
            continue
        if not desc or (debit == 0 and credit == 0):
            continue
        rows.append({"date": d, "description": desc, "amount": credit if credit and not debit else debit,
                     "is_income": bool(credit and not debit), "txn_ref": _pick(row, "txn_ref")})
    return rows
