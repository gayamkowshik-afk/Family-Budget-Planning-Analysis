"""Recruiter note: the single path every transaction takes into the database, whether typed in by
hand or uploaded as a CSV: clean -> remove duplicates -> categorize -> save."""
from sqlalchemy.orm import Session

from ..models import Transaction, User
from .categorizer import categorize
from .cleaning import dedupe_key, normalize_merchant


def ingest(db: Session, user: User, rows: list[dict], source: str) -> dict:
    existing = {dedupe_key(t.date, t.description, t.amount)
                for t in db.query(Transaction).filter_by(family_id=user.family_id)}
    added = skipped = 0
    for r in rows:
        key = dedupe_key(r["date"], r["description"], r["amount"])
        if key in existing:
            skipped += 1
            continue
        existing.add(key)
        category, conf = r.get("category"), 1.0
        if r.get("is_income"):
            category = "Income"
        if not category:
            category, conf, _ = categorize(r["description"])
        db.add(Transaction(family_id=user.family_id, date=r["date"], description=r["description"].strip(),
                           merchant=normalize_merchant(r["description"]), amount=r["amount"], category=category,
                           payment_mode=r.get("payment_mode", "UPI"), txn_ref=r.get("txn_ref", ""),
                           source=source, confidence=conf))
        added += 1
    db.commit()
    return {"added": added, "skipped_duplicates": skipped}
