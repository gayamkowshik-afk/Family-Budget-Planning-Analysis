"""Recruiter note: the database tables. Everything is tied to a family_id, so one family can
never see another family's data. Child tables are separate because children get their own
transparent wallet instead of being secretly tracked."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Family(Base):
    __tablename__ = "families"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"))


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(300))
    merchant: Mapped[str] = mapped_column(String(120), default="")
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50), index=True)
    payment_mode: Mapped[str] = mapped_column(String(20), default="UPI")
    txn_ref: Mapped[str] = mapped_column(String(60), default="", index=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual / csv / mock
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)  # how sure the categorizer was


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    limit_amount: Mapped[float] = mapped_column(Float)


class PricePoint(Base):
    __tablename__ = "price_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    product: Mapped[str] = mapped_column(String(50), index=True)
    store: Mapped[str] = mapped_column(String(60))
    price: Mapped[float] = mapped_column(Float)  # price per standard unit (kg / litre)
    date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(20), default="govt")  # govt / crowd / synthetic


class Child(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    allowance: Mapped[float] = mapped_column(Float)
    balance: Mapped[float] = mapped_column(Float)
    consent_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # proof of consent


class ChildLimit(Base):
    __tablename__ = "child_limits"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    limit_amount: Mapped[float] = mapped_column(Float)


class ChildSpend(Base):
    __tablename__ = "child_spends"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[date] = mapped_column(Date, default=date.today)


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    target: Mapped[float] = mapped_column(Float)
    saved: Mapped[float] = mapped_column(Float, default=0)
