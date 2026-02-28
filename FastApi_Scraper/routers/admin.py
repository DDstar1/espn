from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from db.database import get_db
from models.orm import Tracker, ZSiteExecutablesMeta, ZSiteSportyFixtures
from models.schemas import TrackerSchema, ZSiteExecutablesMetaSchema, ZSiteSportyFixturesSchema

router = APIRouter()


# ── Tracker ───────────────────────────────────────────────────────────────────

@router.get("/tracker", response_model=List[TrackerSchema])
async def get_tracker_entries(
    status: Optional[str] = Query(None, description="Filter by status"),
    worker: Optional[str] = Query(None, description="Filter by worker name"),
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Tracker)
    if status:
        query = query.where(Tracker.status == status)
    if worker:
        query = query.where(Tracker.worker == worker)
    query = query.order_by(Tracker.scraped_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/tracker/{tracker_id}", response_model=TrackerSchema)
async def get_tracker_entry(tracker_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tracker).where(Tracker.id == tracker_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Tracker entry not found")
    return row


# ── Z Site: Executables Meta ──────────────────────────────────────────────────

@router.get("/z/executables", response_model=List[ZSiteExecutablesMetaSchema])
async def get_executables(
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ZSiteExecutablesMeta)
    if name:
        query = query.where(ZSiteExecutablesMeta.name.ilike(f"%{name}%"))
    query = query.order_by(ZSiteExecutablesMeta.uploaded_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/z/executables/{executable_id}", response_model=ZSiteExecutablesMetaSchema)
async def get_executable(executable_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ZSiteExecutablesMeta).where(ZSiteExecutablesMeta.id == executable_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Executable not found")
    return row


# ── Z Site: Sporty Fixtures ───────────────────────────────────────────────────

@router.get("/z/fixtures", response_model=List[ZSiteSportyFixturesSchema])
async def get_sporty_fixtures(
    tournament: Optional[str] = Query(None, description="Filter by tournament name"),
    team: Optional[str] = Query(None, description="Filter by home or away team name"),
    status: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None, description="Start time filter (ISO format)"),
    to_time: Optional[datetime] = Query(None, description="End time filter (ISO format)"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(ZSiteSportyFixtures)
    if tournament:
        query = query.where(ZSiteSportyFixtures.tournament_name.ilike(f"%{tournament}%"))
    if team:
        query = query.where(
            ZSiteSportyFixtures.home_team.ilike(f"%{team}%")
            | ZSiteSportyFixtures.away_team.ilike(f"%{team}%")
        )
    if status:
        query = query.where(ZSiteSportyFixtures.status == status)
    if from_time:
        query = query.where(ZSiteSportyFixtures.start_time >= from_time)
    if to_time:
        query = query.where(ZSiteSportyFixtures.start_time <= to_time)

    query = query.order_by(ZSiteSportyFixtures.start_time.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/z/fixtures/{fixture_id}", response_model=ZSiteSportyFixturesSchema)
async def get_sporty_fixture(fixture_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ZSiteSportyFixtures).where(ZSiteSportyFixtures.id == fixture_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return row
