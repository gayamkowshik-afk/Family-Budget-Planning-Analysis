"""Recruiter note: the entry point of the API. Run it and open /docs to see every endpoint
with a built-in "try it" screen (Swagger)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (registers the tables)
from .database import Base, engine
from .routers import analytics, auth, children, prices, transactions
from .services import categorizer

Base.metadata.create_all(engine)
categorizer.load_model()  # loads the trained ML model if the pipeline has produced one

app = FastAPI(title="FamilyFinance Pro API", version="1.0",
              description="Family budget analytics, price-timing advice and a child money wallet.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # tighten in production
for r in (auth, transactions, analytics, prices, children):
    app.include_router(r.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "ml_model_loaded": categorizer.model_loaded()}
