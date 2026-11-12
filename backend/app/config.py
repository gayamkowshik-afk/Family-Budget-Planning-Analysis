"""Recruiter note: all settings live here and come from environment variables,
so the same code runs on my laptop (SQLite) and in Docker (PostgreSQL) without edits."""
import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./familyfinance.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")  # never commit a real key
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "120"))
DEMO_OTP = os.getenv("DEMO_OTP", "123456")  # used by the mock payment gateway only
MODEL_PATH = Path(os.getenv("MODEL_PATH", Path(__file__).resolve().parents[1] / "models" / "categorizer.joblib"))
