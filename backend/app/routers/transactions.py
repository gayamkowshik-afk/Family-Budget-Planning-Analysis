"""Recruiter note: the three ways money data gets in: type it, upload a statement, or verify a
payment with an ID and OTP (mock gateway)."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Transaction, User
from ..schemas import TxIn, TxOut, VerifyIn
from ..security import current_user
from ..services import mock_gateway
from ..services.cleaning import parse_statement
from ..services.ingest import ingest

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", status_code=201)
def add(body: TxIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return ingest(db, user, [body.model_dump()], source="manual")


@router.get("", response_model=list[TxOut])
def list_all(limit: int = 100, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return (db.query(Transaction).filter_by(family_id=user.family_id)
            .order_by(Transaction.date.desc()).limit(min(limit, 500)).all())


@router.post("/upload")
async def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    text = (await file.read()).decode("utf-8-sig", errors="ignore")
    rows = parse_statement(text)
    if not rows:
        raise HTTPException(422, "No readable rows. Expected columns like date, description, amount.")
    return {**ingest(db, user, rows, source="csv"), "rows_read": len(rows)}


@router.post("/verify")
def verify(body: VerifyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter_by(family_id=user.family_id, txn_ref=body.txn_ref).first()
    if not tx:
        raise HTTPException(404, "No transaction with that ID. Add it or upload a statement first.")
    if not mock_gateway.check_otp(body.otp):
        raise HTTPException(401, "Wrong OTP")
    tx.verified = True
    db.commit()
    return {"txn_ref": body.txn_ref, "verified": True}
