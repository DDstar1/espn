from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# Shared config — tells Pydantic to read from ORM attributes
class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Team ──────────────────────────────────────────────────────────────────────

class TeamSchema(ORMBase):
    espn_id: int
    name: str
    logo: str


# ── Player ────────────────────────────────────────────────────────────────────

class PlayerSchema(ORMBase):
    espn_id: int
    name: str
    dob: Optional[str] = None
    nationality: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None


# ── Game Info ─────────────────────────────────────────────────────────────────

class GameInfoSchema(ORMBase):
    espn_id: int
    date: str
    referee: Optional[str] = None
    place: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    commentary: Optional[Any] = None
    attendance: Optional[int] = None
    league_name: Optional[str] = None
    league_id: Optional[str] = None


# ── Team Game History ─────────────────────────────────────────────────────────

class TeamGameHistorySchema(ORMBase):
    id: int
    espn_team_id: int
    espn_game_info_id: int
    formation: Optional[str] = None
    goals: int
    league_stats: Optional[Any] = None


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalSchema(ORMBase):
    id: int
    team_game_history_id: int
    espn_player_id: int
    time: str
    own_goal: bool


# ── Fouls ─────────────────────────────────────────────────────────────────────

class FoulSchema(ORMBase):
    id: int
    team_game_history_id: int
    espn_player_id: int
    card_type: str
    time: str


# ── Offside ───────────────────────────────────────────────────────────────────

class OffsideSchema(ORMBase):
    id: int
    team_game_history_id: int
    espn_player_id: int
    time: str


# ── Free Kick ─────────────────────────────────────────────────────────────────

class FreeKickSchema(ORMBase):
    id: int
    team_game_history_id: int
    time: str
    attacker_espn_id: int
    attacker_style: str
    attacked_from: str
    saved_at: str


# ── Team Statistics ───────────────────────────────────────────────────────────

class TeamStatisticsSchema(ORMBase):
    id: int
    team_game_history_id: int
    shot_on_goals: Optional[int] = None
    shot_attempts: Optional[int] = None
    fouls: Optional[int] = None
    goals: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    corner_kicks: Optional[int] = None
    saves: Optional[int] = None
    possession_percent: Optional[float] = None


# ── Line Up Statistics ────────────────────────────────────────────────────────

class LineUpStatisticsSchema(ORMBase):
    id: int
    team_game_history_id: int
    espn_player_id: int
    player_num: Optional[int] = None
    formation_position: Optional[int] = None
    goals: Optional[int] = None
    owngoals: Optional[int] = None
    saves: Optional[int] = None
    shots: Optional[int] = None
    shots_on_target: Optional[int] = None
    fouls_commited: Optional[int] = None
    fouls_suffered: Optional[int] = None
    assists: Optional[int] = None
    offsides: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    unused_player: Optional[bool] = None
    subbed_out_in_min: Optional[int] = None
    subbed_in_player: Optional[int] = None


# ── Tracker ───────────────────────────────────────────────────────────────────

class TrackerSchema(ORMBase):
    id: int
    scraped_team_url: str
    scraped_at: datetime
    status: str
    worker: str


# ── Z Site: Executables Meta ──────────────────────────────────────────────────

class ZSiteExecutablesMetaSchema(ORMBase):
    id: UUID
    name: str
    url: str
    description: Optional[str] = None
    uploaded_at: Optional[datetime] = None


# ── Z Site: Sporty Fixtures ───────────────────────────────────────────────────

class ZSiteSportyFixturesSchema(ORMBase):
    id: int
    tournament_name: str
    home_team: str
    home_team_logo: Optional[str] = None
    away_team: str
    away_team_logo: Optional[str] = None
    start_time: Optional[datetime] = None
    sporty_match_id: Optional[str] = None
    status: Optional[str] = None
    markets: Optional[Any] = None
    scraped_at: datetime
