"""Recruiter note: a stand-in for a real payment/bank verification service. Real banks do not let a
student project pull history from a transaction ID, and India's Account Aggregator network needs a
licence. So this mock shows the verification flow (ID + OTP) behind a clean function; a real
provider could replace it later without touching the rest of the app."""
from ..config import DEMO_OTP


def check_otp(otp: str) -> bool:
    return otp == DEMO_OTP
