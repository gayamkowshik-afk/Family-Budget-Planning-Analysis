"""Recruiter note: trains the model that sorts transactions into categories (TF-IDF text features +
logistic regression). The final app uses rules first, then this model for merchants the rules have
never seen. Test rows are held out, and I compare rules-only vs rules+ML. Honest caveat: the data is
synthetic, so scores are optimistic; real labelled statements are the next test."""
import re

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from common import PROCESSED, REPORTS, ROOT
from app.services import categorizer


def clean_text(s: str) -> str:
    return re.sub(r"\d+", " ", s.lower())


def main():
    df = pd.read_csv(PROCESSED / "transactions.csv")
    df = df[df["category"] != "Income"]
    X, y = df["description"].map(clean_text), df["category"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)), LogisticRegression(max_iter=2000, C=5))
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    categorizer._model = None
    base = [categorizer.categorize(t)[0] for t in Xte]  # rules only (the baseline)
    joblib.dump(model, ROOT / "backend" / "models" / "categorizer.joblib")
    categorizer.load_model()
    hybrid = [categorizer.categorize(t)[0] for t in Xte]  # rules first, ML for the rest (what the app does)
    metrics = {"rules_only_accuracy": round(accuracy_score(yte, base), 4), "rules_plus_ml_accuracy": round(accuracy_score(yte, hybrid), 4),
               "ml_alone_accuracy": round(accuracy_score(yte, pred), 4), "ml_alone_macro_f1": round(f1_score(yte, pred, average="macro"), 4), "test_rows": len(yte)}
    print(metrics)
    print(classification_report(yte, pred, zero_division=0))
    pd.DataFrame([metrics]).to_csv(REPORTS / "categorizer_metrics.csv", index=False)
    print("model saved to backend/models/categorizer.joblib")


if __name__ == "__main__":
    main()
