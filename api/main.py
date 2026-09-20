"""
api/main.py

FastAPI application entrypoint.

Run:
    uvicorn api.main:app --reload
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="Road Health Score Prediction API — Module 2",
    description=(
        "Module 2 of the AI-Based Road Health Score Prediction System for "
        "Tamil Nadu. Consumes structured road observation data from Module 1, "
        "predicts a Road Health Score (0-100) via a trained ML model, and "
        "produces congestion / accident-risk / maintenance-priority outputs "
        "via transparent rule-based logic, for consumption by the Module 3 "
        "GIS dashboard."
    ),
    version="1.0.0",
)

# Allow the Module 3 dashboard (likely a different origin during dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to the actual dashboard origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Road Health Score Prediction API — Module 2",
        "docs": "/docs",
    }
