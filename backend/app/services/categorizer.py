"""Recruiter note: two-step auto-categorization. Step 1 is fast, explainable keyword rules.
Step 2 is a machine-learning model (trained in /pipeline) for anything the rules miss.
Each answer carries a confidence score so low-confidence rows can be shown to the user for review."""
import re

from ..config import MODEL_PATH

RULES = {
    "Income": ["salary", "refund", "interest credit"],
    "Groceries": ["rice", "dal", "atta", "oil", "milk", "dmart", "bigbasket", "blinkit", "kirana", "grocery"],
    "Vegetables": ["sabzi", "onion", "tomato", "vegetable", "fruit"],
    "Dining": ["swiggy", "zomato", "restaurant", "cafe", "pizza"],
    "Transport": ["uber", "ola ", "metro", "petrol", "fuel"],
    "Utilities": ["electricity", "recharge", "gas cylinder", "broadband", "water bill", "jio", "bescom", "mseb"],
    "Rent": ["rent"],
    "Education": ["school", "tuition", "fees"],
    "Health": ["pharmacy", "medical", "doctor", "hospital"],
    "Entertainment": ["netflix", "spotify", "movie", "hotstar", "prime video"],
    "Shopping": ["amzn", "amazon", "flipkart", "myntra"],
}
_model = None


def load_model(path=MODEL_PATH):
    global _model
    try:
        import joblib
        _model = joblib.load(path)
    except Exception:
        _model = None  # the app still works with rules only


def model_loaded() -> bool:
    return _model is not None


def categorize(description: str):
    """Returns (category, confidence, method)."""
    low = description.lower()
    for category, words in RULES.items():
        if any(w in low for w in words):
            return category, 0.95, "rule"
    if _model is not None:
        probs = _model.predict_proba([re.sub(r"\d+", " ", low)])[0]
        i = probs.argmax()
        return _model.classes_[i], float(probs[i]), "ml"
    return "Others", 0.3, "default"
