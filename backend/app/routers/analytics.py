"""Recruiter note: the insight endpoints the dashboard reads from."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Budget, Transaction, User
from ..schemas import BudgetIn
from ..security import current_user
from ..services import insights

router = APIRouter(tags=["analytics"])


def _txs(db, user):
    return db.query(Transaction).filter_by(family_id=user.family_id).all()


def _budgets(db, user):
    return {b.category: b.limit_amount for b in db.query(Budget).filter_by(family_id=user.family_id)}


@router.get("/analytics/summary")
def summary(month: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    return insights.monthly_summary(_txs(db, user), month or date.today().strftime("%Y-%m"))


@router.get("/analytics/anomalies")
def anomalies(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return insights.find_anomalies(_txs(db, user))


@router.get("/analytics/recurring")
def recurring(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return insights.find_recurring(_txs(db, user))


@router.get("/analytics/health-score")
def health(month: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = insights.monthly_summary(_txs(db, user), month or date.today().strftime("%Y-%m"))
    return insights.health_score(s, _budgets(db, user))


@router.put("/budgets")
def set_budget(body: BudgetIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.query(Budget).filter_by(family_id=user.family_id, category=body.category).first()
    if b:
        b.limit_amount = body.limit_amount
    else:
        db.add(Budget(family_id=user.family_id, category=body.category, limit_amount=body.limit_amount))
    db.commit()
    return _budgets(db, user)


@router.get("/budgets/status")
def budget_status(month: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = insights.monthly_summary(_txs(db, user), month or date.today().strftime("%Y-%m"))
    return [{"category": c, "limit": lim, "spent": s["by_category"].get(c, 0),
             "used_pct": round(s["by_category"].get(c, 0) / lim * 100) if lim else None}
            for c, lim in _budgets(db, user).items()]
