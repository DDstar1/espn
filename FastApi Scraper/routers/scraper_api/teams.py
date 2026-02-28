from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.orm import Team
from routers.scraper_api.schemas import (
    TeamInsertRequest, TeamExistsResponse, InsertResponse
)

router = APIRouter(prefix="/teams", tags=["Scraper · Teams"])


@router.get("/{espn_id}/exists", response_model=TeamExistsResponse)
async def team_exists(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Mirrors: team_exists(espn_id)"""
    result = await db.execute(select(Team.espn_id).where(Team.espn_id == espn_id))
    return {"espn_id": espn_id, "exists": result.scalar_one_or_none() is not None}


@router.post("/insert", response_model=InsertResponse)
async def insert_team(body: TeamInsertRequest, db: AsyncSession = Depends(get_db)):
    """
    Mirrors: insert_team(data)
    Only inserts if the team does not already exist. Safe to call repeatedly.
    """
    result = await db.execute(select(Team.espn_id).where(Team.espn_id == body.espn_id))
    if result.scalar_one_or_none() is not None:
        return {"success": True, "message": f"Team {body.espn_id} already exists, skipped."}

    db.add(Team(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": f"Team {body.espn_id} inserted."}
