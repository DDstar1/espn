from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from db.database import get_db
from models.orm import TeamStatistics, LineUpStatistics, TeamGameHistory, GameInfo
from models.schemas import TeamStatisticsSchema, LineUpStatisticsSchema

router = APIRouter()


# ── Team Statistics ───────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/statistics", response_model=TeamStatisticsSchema)
async def get_team_statistics(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamStatistics).where(TeamStatistics.team_game_history_id == tgh_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Statistics not found")
    return row


@router.get("/games/{espn_id}/statistics", response_model=List[TeamStatisticsSchema])
async def get_game_statistics(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Team-level stats for both sides in a game."""
    result = await db.execute(
        select(TeamStatistics)
        .join(TeamGameHistory, TeamGameHistory.id == TeamStatistics.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Statistics not found for this game")
    return rows


# ── Line Up Statistics ────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/lineup", response_model=List[LineUpStatisticsSchema])
async def get_lineup(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LineUpStatistics)
        .where(LineUpStatistics.team_game_history_id == tgh_id)
        .order_by(LineUpStatistics.unused_player.asc(), LineUpStatistics.formation_position.asc())
    )
    return result.scalars().all()


@router.get("/games/{espn_id}/lineups", response_model=List[LineUpStatisticsSchema])
async def get_game_lineups(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Full lineups for both teams in a game."""
    result = await db.execute(
        select(LineUpStatistics)
        .join(TeamGameHistory, TeamGameHistory.id == LineUpStatistics.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
        .order_by(
            TeamGameHistory.espn_team_id,
            LineUpStatistics.unused_player.asc(),
            LineUpStatistics.formation_position.asc(),
        )
    )
    return result.scalars().all()


@router.get("/players/{espn_player_id}/stats", response_model=List[LineUpStatisticsSchema])
async def get_player_stats(
    espn_player_id: int,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """All match stats for a player, newest game first."""
    result = await db.execute(
        select(LineUpStatistics)
        .join(TeamGameHistory, TeamGameHistory.id == LineUpStatistics.team_game_history_id)
        .join(GameInfo, GameInfo.espn_id == TeamGameHistory.espn_game_info_id)
        .where(LineUpStatistics.espn_player_id == espn_player_id)
        .order_by(GameInfo.date.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
