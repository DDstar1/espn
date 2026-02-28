from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from db.database import get_db
from models.orm import Team, Player
from models.schemas import TeamSchema, PlayerSchema

router = APIRouter()


# ── Teams ─────────────────────────────────────────────────────────────────────

@router.get("/teams", response_model=List[TeamSchema])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()


@router.get("/teams/{espn_id}", response_model=TeamSchema)
async def get_team(espn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.espn_id == espn_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# ── Players ───────────────────────────────────────────────────────────────────

@router.get("/players", response_model=List[PlayerSchema])
async def get_players(
    name: Optional[str] = Query(None, description="Filter by player name (partial match)"),
    nationality: Optional[str] = Query(None),
    limit: int = Query(50, le=2000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Player)
    if name:
        query = query.where(Player.name.ilike(f"%{name}%"))
    if nationality:
        query = query.where(Player.nationality.ilike(f"%{nationality}%"))
    query = query.order_by(Player.name).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/players/{espn_id}", response_model=PlayerSchema)
async def get_player(espn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.espn_id == espn_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
