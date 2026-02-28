from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from db.database import get_db
from models.orm import GameInfo, TeamGameHistory
from models.schemas import GameInfoSchema, TeamGameHistorySchema

router = APIRouter()


# ── Game Info ─────────────────────────────────────────────────────────────────

@router.get("/games", response_model=List[GameInfoSchema])
async def get_games(
    league_id: Optional[str] = Query(None),
    league_name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(GameInfo)
    if league_id:
        query = query.where(GameInfo.league_id == league_id)
    if league_name:
        query = query.where(GameInfo.league_name.ilike(f"%{league_name}%"))
    if country:
        query = query.where(GameInfo.country.ilike(f"%{country}%"))
    query = query.order_by(GameInfo.date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/games/{espn_id}", response_model=GameInfoSchema)
async def get_game(espn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GameInfo).where(GameInfo.espn_id == espn_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


# ── Team Game History ─────────────────────────────────────────────────────────

@router.get("/games/{espn_id}/teams", response_model=List[TeamGameHistorySchema])
async def get_game_team_histories(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Both teams and their records for a specific game."""
    result = await db.execute(
        select(TeamGameHistory).where(TeamGameHistory.espn_game_info_id == espn_id)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No team history found for this game")
    return rows


@router.get("/team-history/{tgh_id}", response_model=TeamGameHistorySchema)
async def get_team_game_history(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamGameHistory).where(TeamGameHistory.id == tgh_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Team game history not found")
    return row


@router.get("/teams/{espn_team_id}/history", response_model=List[TeamGameHistorySchema])
async def get_team_history(
    espn_team_id: int,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """All game history for a team, newest first."""
    result = await db.execute(
        select(TeamGameHistory)
        .join(GameInfo, GameInfo.espn_id == TeamGameHistory.espn_game_info_id)
        .where(TeamGameHistory.espn_team_id == espn_team_id)
        .order_by(GameInfo.date.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
