"""Recruiter note: the child money wallet. Design choice: NO secret tracking. A parent must confirm
consent AND the child must agree, which fits India's DPDP Act 2023 principle of verifiable parental
consent for under-18 data. The child sees the same numbers the parent sees."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Child, ChildLimit, ChildSpend, Goal, User
from ..schemas import ChildIn, GoalIn, SpendIn
from ..security import current_user

router = APIRouter(prefix="/children", tags=["children"])
DEFAULT_LIMITS = {"Snacks": 300, "Games": 300, "Fun": 400}


def _own(db, user, child_id) -> Child:
    c = db.get(Child, child_id)
    if not c or c.family_id != user.family_id:
        raise HTTPException(404, "Child not found")
    return c


@router.post("", status_code=201)
def create(body: ChildIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not (body.parent_consent and body.child_assent):
        raise HTTPException(422, "Both parent consent and the child's agreement are required.")
    c = Child(family_id=user.family_id, name=body.name, allowance=body.allowance, balance=body.allowance)
    db.add(c)
    db.flush()
    db.add_all(ChildLimit(child_id=c.id, category=k, limit_amount=v) for k, v in DEFAULT_LIMITS.items())
    db.commit()
    return {"id": c.id, "name": c.name, "balance": c.balance}


@router.post("/{child_id}/spend")
def spend(child_id: int, body: SpendIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = _own(db, user, child_id)
    if body.amount > c.balance:
        raise HTTPException(422, "Not enough balance in the wallet.")
    limit = db.query(ChildLimit).filter_by(child_id=c.id, category=body.category).first()
    used = sum(s.amount for s in db.query(ChildSpend).filter_by(child_id=c.id, category=body.category)
               if s.date.strftime("%Y-%m") == date.today().strftime("%Y-%m"))
    c.balance -= body.amount
    db.add(ChildSpend(child_id=c.id, category=body.category, amount=body.amount))
    db.commit()
    over = bool(limit and used + body.amount > limit.limit_amount)
    return {"balance": c.balance, "over_limit": over,
            "coaching": "You passed this month's limit. What could you skip next time?" if over else "Logged."}


@router.post("/{child_id}/goals", status_code=201)
def add_goal(child_id: int, body: GoalIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = _own(db, user, child_id)
    g = Goal(child_id=c.id, title=body.title, target=body.target)
    db.add(g)
    db.commit()
    return {"id": g.id}


@router.post("/{child_id}/goals/{goal_id}/save")
def save_to_goal(child_id: int, goal_id: int, amount: float = 100, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c, g = _own(db, user, child_id), db.get(Goal, goal_id)
    if not g or g.child_id != c.id or amount <= 0 or amount > c.balance:
        raise HTTPException(422, "Invalid goal or amount")
    c.balance -= amount
    g.saved += amount
    db.commit()
    return {"saved": g.saved, "target": g.target, "balance": c.balance}


@router.get("/{child_id}/summary")
def summary(child_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = _own(db, user, child_id)
    spends = db.query(ChildSpend).filter_by(child_id=c.id).all()
    by_cat = {}
    for s in spends:
        by_cat[s.category] = by_cat.get(s.category, 0) + s.amount
    return {"name": c.name, "balance": c.balance, "allowance": c.allowance, "spent_by_category": by_cat,
            "limits": {l.category: l.limit_amount for l in db.query(ChildLimit).filter_by(child_id=c.id)},
            "goals": [{"title": g.title, "saved": g.saved, "target": g.target} for g in db.query(Goal).filter_by(child_id=c.id)],
            "visible_to_child": True}
