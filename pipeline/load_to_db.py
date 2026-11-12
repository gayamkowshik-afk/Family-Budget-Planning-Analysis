"""Recruiter note: loads the cleaned data into the app's database and creates a demo login
(demo@familyfinance.dev / demo1234) so the dashboard has something to show straight away."""
import pandas as pd

from common import PROCESSED
from app import models  # noqa: F401
from app.database import Base, SessionLocal, engine
from app.models import Budget, Family, PricePoint, Transaction, User
from app.security import hash_password


def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(User).filter_by(email="demo@familyfinance.dev").first():
        print("demo data already loaded")
        return
    fam = Family(name="Demo family")
    db.add(fam)
    db.flush()
    db.add(User(name="Demo Parent", email="demo@familyfinance.dev", password_hash=hash_password("demo1234"), family_id=fam.id))
    tx = pd.read_csv(PROCESSED / "transactions.csv", parse_dates=["date"])
    db.add_all(Transaction(family_id=fam.id, date=r.date.date(), description=r.description, merchant=r.merchant,
                           amount=float(r.amount), category=r.category, txn_ref=str(r.txn_ref) if pd.notna(r.txn_ref) else "",
                           source="pipeline", verified=False) for r in tx.itertuples())
    pr = pd.read_csv(PROCESSED / "prices.csv", parse_dates=["date"])
    db.add_all(PricePoint(product=r.product, store=r.store, price=float(r.price), date=r.date.date(), source=r.source) for r in pr.itertuples())
    db.add_all(Budget(family_id=fam.id, category=c, limit_amount=v) for c, v in
               {"Groceries": 8000, "Vegetables": 2500, "Dining": 4500, "Transport": 4500, "Utilities": 5000, "Entertainment": 1000, "Shopping": 4000}.items())
    db.commit()
    print(f"loaded {len(tx)} transactions and {len(pr)} price points")


if __name__ == "__main__":
    main()
