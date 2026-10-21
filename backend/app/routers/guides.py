"""Guide directory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_session
from app.models import Guide
from app.schemas import GuideDetail, GuideListResponse
from app.seed import SETUP_PATHS
from app.serialize import guide_detail, guide_summary

router = APIRouter(tags=["guides"])


@router.get("/guides", response_model=GuideListResponse)
def list_guides(
    q: str | None = Query(default=None, max_length=120),
    path: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> GuideListResponse:
    if path is not None and path not in SETUP_PATHS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_path",
                "message": "Unknown setup path filter.",
                "allowed": sorted(SETUP_PATHS),
            },
        )

    statement = select(Guide).order_by(Guide.name.asc())
    needle = (q or "").strip().lower()
    if needle:
        like = f"%{needle}%"
        statement = statement.where(
            or_(
                func.lower(Guide.name).like(like),
                func.lower(Guide.slug).like(like),
                func.lower(Guide.summary).like(like),
            )
        )
    if path is not None:
        statement = statement.where(Guide.setup_path == path)

    guides = session.scalars(statement).all()
    summaries = [guide_summary(guide) for guide in guides]
    return GuideListResponse(guides=summaries, count=len(summaries))


@router.get("/guides/{slug}", response_model=GuideDetail)
def get_guide(slug: str, session: Session = Depends(get_session)) -> GuideDetail:
    statement = (
        select(Guide)
        .where(Guide.slug == slug)
        .options(selectinload(Guide.items), selectinload(Guide.sources))
    )
    guide = session.scalar(statement)
    if guide is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": "No guide exists for this address.",
                "slug": slug,
            },
        )
    return guide_detail(guide)
