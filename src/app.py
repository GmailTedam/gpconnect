"""Standalone 3-Tier FastAPI Service for gpconnect (gpconnect)."""

from __future__ import annotations

from pathlib import Path as _CohortPath
from fastapi import FastAPI

try:
    from .clinical_cohort_3tier_router import build_clinical_cohort_3tier_router as _build_cohort_3tier_router
except ImportError:
    from clinical_cohort_3tier_router import build_clinical_cohort_3tier_router as _build_cohort_3tier_router

app = FastAPI(title="gpconnect", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gpconnect", "sibling_slug": "gpconnect"}


app.include_router(
    _build_cohort_3tier_router(
        service_name="gpconnect",
        sibling_slug="gpconnect",
        repo_root=_CohortPath(__file__).resolve().parents[1],
    )
)
