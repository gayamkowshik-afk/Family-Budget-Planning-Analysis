"""Recruiter note: request/response shapes. Pydantic validates every input,
so bad data is rejected before it reaches the database."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)


class TxIn(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=300)
    amount: float = Field(gt=0)
    category: Optional[str] = None
    txn_ref: str = ""
    payment_mode: str = "UPI"
    is_income: bool = False


class TxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    description: str
    merchant: str
    amount: float
    category: str
    verified: bool
    confidence: float
    source: str


class VerifyIn(BaseModel):
    txn_ref: str
    otp: str


class BudgetIn(BaseModel):
    category: str
    limit_amount: float = Field(ge=0)


class PriceIn(BaseModel):
    product: str
    store: str
    price: float = Field(gt=0)
    date: Optional[date] = None


class ChildIn(BaseModel):
    name: str
    allowance: float = Field(ge=0)
    parent_consent: bool
    child_assent: bool  # the child agrees too: part of the "no secret tracking" design


class SpendIn(BaseModel):
    category: str
    amount: float = Field(gt=0)


class GoalIn(BaseModel):
    title: str
    target: float = Field(gt=0)
