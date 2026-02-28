from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.orm import LineUpStatistics
from routers.scraper_api.schemas import (
    LineUpStatisticsUpsertRequest, LineUpExistsResponse, InsertResponse
)

router = APIRouter(prefix="/lineup-statistics", tags=["Scraper · Lineup Statistics"])


@router.get("/exists", response_model=LineUpExistsResponse)
async def player_lineup_stat_exists(
    team_game_history_id: int,
    espn_player_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Mirrors: player_line_up_stat_exists(team_game_history_id, espn_player_id)
    Pass both as query params: ?team_game_history_id=X&espn_player_id=Y
    """
    result = await db.execute(
        select(LineUpStatistics.id)
        .where(LineUpStatistics.team_game_history_id == team_game_history_id)
        .where(LineUpStatistics.espn_player_id == espn_player_id)
        .limit(1)
    )
    return {
        "team_game_history_id": team_game_history_id,
        "espn_player_id": espn_player_id,
        "exists": result.scalar_one_or_none() is not None,
    }


@router.post("/upsert", response_model=InsertResponse)
async def upsert_lineup_statistics(
    body: LineUpStatisticsUpsertRequest, db: AsyncSession = Depends(get_db)
):
    """
    Mirrors: insert_line_up_statistics(data)
    Upserts on (team_game_history_id, espn_player_id).
    """
    result = await db.execute(
        select(LineUpStatistics)
        .where(LineUpStatistics.team_game_history_id == body.team_game_history_id)
        .where(LineUpStatistics.espn_player_id == body.espn_player_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for field, value in body.model_dump().items():
            setattr(existing, field, value)
        msg = "Lineup statistics updated."
    else:
        db.add(LineUpStatistics(**body.model_dump()))
        msg = "Lineup statistics inserted."

    await db.commit()
    return {"success": True, "message": msg}
