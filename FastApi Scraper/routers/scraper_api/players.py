from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.orm import Player
from routers.scraper_api.schemas import (
    PlayerUpsertRequest, PlayerExistsResponse, InsertResponse
)

router = APIRouter(prefix="/players", tags=["Scraper · Players"])


@router.get("/{espn_id}/exists", response_model=PlayerExistsResponse)
async def player_exists(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Mirrors: player_exists(espn_id)"""
    result = await db.execute(select(Player.espn_id).where(Player.espn_id == espn_id))
    return {"espn_id": espn_id, "exists": result.scalar_one_or_none() is not None}


@router.post("/upsert", response_model=InsertResponse)
async def upsert_player(body: PlayerUpsertRequest, db: AsyncSession = Depends(get_db)):
    """Mirrors: insert_player(data) — uses upsert so safe to call repeatedly."""
    result = await db.execute(select(Player).where(Player.espn_id == body.espn_id))
    player = result.scalar_one_or_none()

    if player:
        for field, value in body.model_dump().items():
            setattr(player, field, value)
    else:
        db.add(Player(**body.model_dump()))

    await db.commit()
    return {"success": True, "message": f"Player {body.espn_id} upserted."}
