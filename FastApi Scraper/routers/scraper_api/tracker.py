from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import List

from db.database import get_db
from models.orm import Tracker
from models.schemas import TrackerSchema
from routers.scraper_api.schemas import (
    TrackerUpsertRequest, TrackerStatusResponse, InsertResponse
)

router = APIRouter(prefix="/tracker", tags=["Scraper · Tracker"])

LIVE_MINS = 60


# ── Upsert tracker entry ──────────────────────────────────────────────────────

@router.post("/upsert", response_model=InsertResponse)
async def set_latest_scraped_team_url(
    body: TrackerUpsertRequest, db: AsyncSession = Depends(get_db)
):
    """
    Mirrors: set_latest_scraped_team_url(url, status)
    Upserts on scraped_team_url — prevents duplicate rows.
    """
    result = await db.execute(
        select(Tracker).where(Tracker.scraped_team_url == body.scraped_team_url)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.status = body.status
        existing.worker = body.worker
        existing.scraped_at = datetime.now(timezone.utc)
    else:
        db.add(Tracker(
            scraped_team_url=body.scraped_team_url,
            status=body.status,
            worker=body.worker,
            scraped_at=datetime.now(timezone.utc),
        ))

    await db.commit()
    return {"success": True, "message": f"Tracker entry for '{body.scraped_team_url}' upserted."}


# ── Get latest / next team URL to scrape ─────────────────────────────────────

@router.get("/next", response_model=TrackerStatusResponse)
async def get_latest_scraped_team_url(db: AsyncSession = Depends(get_db)):
    """
    Mirrors: get_latest_scraped_team_url()

    Priority order:
    1. Oldest 'processing' entry older than LIVE_MINS (stale — safe to retry)
    2. Most recent 'processing' entry within LIVE_MINS (live — currently being worked)
    3. Most recent 'done' entry (fallback)
    """
    now = datetime.now(timezone.utc)
    live_cutoff = now - timedelta(minutes=LIVE_MINS)

    # 1. Stale processing
    result = await db.execute(
        select(Tracker.scraped_team_url)
        .where(Tracker.status == "processing")
        .where(Tracker.scraped_at <= live_cutoff)
        .order_by(Tracker.scraped_at.asc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return {"status": "stale processing", "scraped_team_url": row}

    # 2. Live processing
    result = await db.execute(
        select(Tracker.scraped_team_url)
        .where(Tracker.status == "processing")
        .where(Tracker.scraped_at >= live_cutoff)
        .order_by(Tracker.scraped_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return {"status": "live processing", "scraped_team_url": row}

    # 3. Fallback: latest done
    result = await db.execute(
        select(Tracker.scraped_team_url)
        .where(Tracker.status == "done")
        .order_by(Tracker.scraped_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return {"status": "done", "scraped_team_url": row}

    return {"status": None, "scraped_team_url": None}


# ── Get all scraped + live team URLs ─────────────────────────────────────────

@router.get("/active-urls", response_model=List[str])
async def get_all_scraped_and_live_teams(db: AsyncSession = Depends(get_db)):
    """
    Mirrors: get_all_scraped_and_live_teams()
    Returns all 'done' URLs + 'processing' URLs scraped within the last LIVE_MINS.
    (The random sleep from the original is intentionally omitted — handle that client-side.)
    """
    now = datetime.now(timezone.utc)
    live_cutoff = (now - timedelta(minutes=LIVE_MINS))

    done = await db.execute(
        select(Tracker.scraped_team_url).where(Tracker.status == "done")
    )
    live = await db.execute(
        select(Tracker.scraped_team_url)
        .where(Tracker.status == "processing")
        .where(Tracker.scraped_at >= live_cutoff)
    )

    done_urls = list(done.scalars().all())
    live_urls = list(live.scalars().all())
    return done_urls + live_urls
