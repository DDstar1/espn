from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.database import get_db
from models.orm import TeamGameHistory
from routers.scraper_api.schemas import (
    TeamGameHistoryUpsertRequest,
    TeamGameHistoryIDResponse,
    InsertResponse,
)

router = APIRouter(prefix="/team-game-history", tags=["Scraper · Team Game History"])


@router.get("/id", response_model=TeamGameHistoryIDResponse)
async def get_team_game_history_id(
    espn_game_info_id: int,
    espn_team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Mirrors: get_team_game_history_id(espn_game_info_id, espn_team_id)
    Returns the internal `id` for a given team + game combination.
    """
    result = await db.execute(
        select(TeamGameHistory.id)
        .where(TeamGameHistory.espn_game_info_id == espn_game_info_id)
        .where(TeamGameHistory.espn_team_id == espn_team_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Team game history not found")
    return {"id": row}


@router.post("/upsert", response_model=TeamGameHistoryIDResponse)
async def upsert_team_game_history(
    body: TeamGameHistoryUpsertRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Mirrors: insert_team_game_history(data)
    Upserts on (espn_team_id, espn_game_info_id) and returns the row's internal id.
    """
    stmt = (
        pg_insert(TeamGameHistory)
        .values(**body.model_dump())
        .on_conflict_do_update(
            index_elements=["espn_team_id", "espn_game_info_id"],
            set_={
                "formation":    body.formation,
                "goals":        body.goals,
                "league_stats": body.league_stats,
            },
        )
        .returning(TeamGameHistory.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    row_id = result.scalar_one()
    return {"id": row_id}
