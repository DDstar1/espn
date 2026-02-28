from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from db.database import get_db
from models.orm import Goal, Foul, Offside, FreeKick, TeamGameHistory
from models.schemas import GoalSchema, FoulSchema, OffsideSchema, FreeKickSchema

router = APIRouter()


# ── Goals ─────────────────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/goals", response_model=List[GoalSchema])
async def get_goals_by_team_history(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Goal).where(Goal.team_game_history_id == tgh_id).order_by(Goal.time)
    )
    return result.scalars().all()


@router.get("/games/{espn_id}/goals", response_model=List[GoalSchema])
async def get_game_goals(
    espn_id: int,
    own_goals_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """All goals in a game. Pass ?own_goals_only=true to filter."""
    query = (
        select(Goal)
        .join(TeamGameHistory, TeamGameHistory.id == Goal.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
    )
    if own_goals_only:
        query = query.where(Goal.own_goal.is_(True))
    query = query.order_by(Goal.time)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/players/{espn_player_id}/goals", response_model=List[GoalSchema])
async def get_player_goals(
    espn_player_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Goal)
        .where(Goal.espn_player_id == espn_player_id)
        .order_by(Goal.time)
    )
    return result.scalars().all()


# ── Fouls ─────────────────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/fouls", response_model=List[FoulSchema])
async def get_fouls_by_team_history(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Foul).where(Foul.team_game_history_id == tgh_id).order_by(Foul.time)
    )
    return result.scalars().all()


@router.get("/games/{espn_id}/fouls", response_model=List[FoulSchema])
async def get_game_fouls(
    espn_id: int,
    card_type: Optional[str] = Query(None, description="e.g. yellow, red"),
    db: AsyncSession = Depends(get_db),
):
    """All fouls/cards in a game. Filter by ?card_type=yellow or ?card_type=red."""
    query = (
        select(Foul)
        .join(TeamGameHistory, TeamGameHistory.id == Foul.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
    )
    if card_type:
        query = query.where(Foul.card_type.ilike(f"%{card_type}%"))
    query = query.order_by(Foul.time)
    result = await db.execute(query)
    return result.scalars().all()


# ── Offsides ──────────────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/offsides", response_model=List[OffsideSchema])
async def get_offsides_by_team_history(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Offside)
        .where(Offside.team_game_history_id == tgh_id)
        .order_by(Offside.time)
    )
    return result.scalars().all()


@router.get("/games/{espn_id}/offsides", response_model=List[OffsideSchema])
async def get_game_offsides(espn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Offside)
        .join(TeamGameHistory, TeamGameHistory.id == Offside.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
        .order_by(Offside.time)
    )
    return result.scalars().all()


# ── Free Kicks ────────────────────────────────────────────────────────────────

@router.get("/team-history/{tgh_id}/free-kicks", response_model=List[FreeKickSchema])
async def get_free_kicks_by_team_history(tgh_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FreeKick)
        .where(FreeKick.team_game_history_id == tgh_id)
        .order_by(FreeKick.time)
    )
    return result.scalars().all()


@router.get("/games/{espn_id}/free-kicks", response_model=List[FreeKickSchema])
async def get_game_free_kicks(espn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FreeKick)
        .join(TeamGameHistory, TeamGameHistory.id == FreeKick.team_game_history_id)
        .where(TeamGameHistory.espn_game_info_id == espn_id)
        .order_by(FreeKick.time)
    )
    return result.scalars().all()
