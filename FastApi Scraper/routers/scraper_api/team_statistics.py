from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.orm import TeamStatistics
from routers.scraper_api.schemas import (
    TeamStatisticsInsertRequest, TeamStatsExistsResponse, InsertResponse
)

router = APIRouter(prefix="/team-statistics", tags=["Scraper · Team Statistics"])


@router.get("/{team_game_history_id}/exists", response_model=TeamStatsExistsResponse)
async def team_stats_exists(
    team_game_history_id: int, db: AsyncSession = Depends(get_db)
):
    """Mirrors: team_stats_exists(team_game_history_id)"""
    result = await db.execute(
        select(TeamStatistics.id)
        .where(TeamStatistics.team_game_history_id == team_game_history_id)
    )
    return {
        "team_game_history_id": team_game_history_id,
        "exists": result.scalar_one_or_none() is not None,
    }


@router.post("/insert", response_model=InsertResponse)
async def insert_team_statistics(
    body: TeamStatisticsInsertRequest, db: AsyncSession = Depends(get_db)
):
    """Mirrors: insert_team_statistics(data)"""
    db.add(TeamStatistics(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": "Team statistics inserted."}
