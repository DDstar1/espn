from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.orm import GameInfo
from routers.scraper_api.schemas import (
    GameInfoInsertRequest, GameInfoExistsResponse, InsertResponse
)

router = APIRouter(prefix="/game-info", tags=["Scraper · Game Info"])


@router.get("/{espn_id}/exists", response_model=GameInfoExistsResponse)
async def game_info_exists(espn_id: int, db: AsyncSession = Depends(get_db)):
    """Mirrors: game_info_exists(espn_id)"""
    result = await db.execute(select(GameInfo.espn_id).where(GameInfo.espn_id == espn_id))
    return {"espn_id": espn_id, "exists": result.scalar_one_or_none() is not None}


@router.post("/insert", response_model=InsertResponse)
async def insert_game_info(body: GameInfoInsertRequest, db: AsyncSession = Depends(get_db)):
    """
    Mirrors: insert_game_info(data)
    Only inserts if not already present.
    """
    result = await db.execute(select(GameInfo.espn_id).where(GameInfo.espn_id == body.espn_id))
    if result.scalar_one_or_none() is not None:
        return {"success": True, "message": f"Game {body.espn_id} already exists, skipped."}

    db.add(GameInfo(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": f"Game {body.espn_id} inserted."}
