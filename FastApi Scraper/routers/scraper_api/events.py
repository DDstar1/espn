from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.orm import Goal, Foul, FreeKick, Offside
from routers.scraper_api.schemas import (
    GoalUpsertRequest,
    FoulUpsertRequest,
    FreeKickInsertRequest,
    OffsideInsertRequest,
    InsertResponse,
)

router = APIRouter(tags=["Scraper · Match Events"])


# ── Goals ─────────────────────────────────────────────────────────────────────

@router.post("/goals/upsert", response_model=InsertResponse)
async def upsert_goal(body: GoalUpsertRequest, db: AsyncSession = Depends(get_db)):
    """Mirrors: insert_goal(data)"""
    db.add(Goal(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": "Goal upserted."}


# ── Fouls ─────────────────────────────────────────────────────────────────────

@router.post("/fouls/upsert", response_model=InsertResponse)
async def upsert_foul(body: FoulUpsertRequest, db: AsyncSession = Depends(get_db)):
    """Mirrors: insert_foul(data)"""
    db.add(Foul(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": "Foul upserted."}


# ── Free Kicks ────────────────────────────────────────────────────────────────

@router.post("/free-kicks/insert", response_model=InsertResponse)
async def insert_free_kick(body: FreeKickInsertRequest, db: AsyncSession = Depends(get_db)):
    """Mirrors: insert_free_kick(data)"""
    db.add(FreeKick(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": "Free kick inserted."}


# ── Offsides ──────────────────────────────────────────────────────────────────

@router.post("/offsides/insert", response_model=InsertResponse)
async def insert_offside(body: OffsideInsertRequest, db: AsyncSession = Depends(get_db)):
    """Mirrors: insert_offside(data)"""
    db.add(Offside(**body.model_dump()))
    await db.commit()
    return {"success": True, "message": "Offside inserted."}
