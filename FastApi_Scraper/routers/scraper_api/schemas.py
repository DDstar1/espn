from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


# ── Player ────────────────────────────────────────────────────────────────────

class PlayerUpsertRequest(BaseModel):
    espn_id: int
    name: str
    dob: Optional[str] = None
    nationality: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None


class PlayerExistsResponse(BaseModel):
    espn_id: int
    exists: bool


# ── Team ──────────────────────────────────────────────────────────────────────

class TeamInsertRequest(BaseModel):
    espn_id: int
    name: str
    logo: str


class TeamExistsResponse(BaseModel):
    espn_id: int
    exists: bool


# ── Game Info ─────────────────────────────────────────────────────────────────

class GameInfoInsertRequest(BaseModel):
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


class GameInfoExistsResponse(BaseModel):
    espn_id: int
    exists: bool


# ── Team Game History ─────────────────────────────────────────────────────────

class TeamGameHistoryUpsertRequest(BaseModel):
    espn_team_id: int
    espn_game_info_id: int
    formation: Optional[str] = None
    goals: int
    league_stats: Optional[Any] = None


class TeamGameHistoryIDResponse(BaseModel):
    id: int


class TeamGameHistoryExistsRequest(BaseModel):
    espn_game_info_id: int
    espn_team_id: int


# ── Team Statistics ───────────────────────────────────────────────────────────

class TeamStatisticsInsertRequest(BaseModel):
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


class TeamStatsExistsResponse(BaseModel):
    team_game_history_id: int
    exists: bool


# ── Line Up Statistics ────────────────────────────────────────────────────────

class LineUpStatisticsUpsertRequest(BaseModel):
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


class LineUpExistsResponse(BaseModel):
    team_game_history_id: int
    espn_player_id: int
    exists: bool


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalUpsertRequest(BaseModel):
    team_game_history_id: int
    espn_player_id: int
    time: str
    own_goal: bool


# ── Fouls ─────────────────────────────────────────────────────────────────────

class FoulUpsertRequest(BaseModel):
    team_game_history_id: int
    espn_player_id: int
    card_type: str
    time: str


# ── Free Kick ─────────────────────────────────────────────────────────────────

class FreeKickInsertRequest(BaseModel):
    team_game_history_id: int
    time: str
    attacker_espn_id: int
    attacker_style: str
    attacked_from: str
    saved_at: str


# ── Offside ───────────────────────────────────────────────────────────────────

class OffsideInsertRequest(BaseModel):
    team_game_history_id: int
    espn_player_id: int
    time: str


# ── Tracker ───────────────────────────────────────────────────────────────────

class TrackerUpsertRequest(BaseModel):
    scraped_team_url: str
    status: str           # "processing" | "done"
    worker: str


class TrackerStatusResponse(BaseModel):
    status: Optional[str]
    scraped_team_url: Optional[str]


# ── Generic ───────────────────────────────────────────────────────────────────

class InsertResponse(BaseModel):
    success: bool
    message: str = ""
