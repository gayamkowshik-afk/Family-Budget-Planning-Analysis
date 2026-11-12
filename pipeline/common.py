"""Recruiter note: shared paths so every pipeline step reads and writes in the same place."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, PROCESSED, REPORTS = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "reports"
for p in (RAW, PROCESSED, REPORTS):
    p.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "backend"))  # lets scripts reuse the backend's cleaning code
