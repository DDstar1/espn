from sqlalchemy import (
    Boolean, Column, Float, Integer, Text, BigInteger,
    ForeignKey, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from db.database import Base


# ── Team ──────────────────────────────────────────────────────────────────────

class Team(Base):
    __tablename__ = "team"

    espn_id = Column(Integer, primary_key=True)
    name    = Column(Text, nullable=False)
    logo    = Column(Text, nullable=False)

    game_histories = relationship("TeamGameHistory", back_populates="team")


# ── Player ────────────────────────────────────────────────────────────────────

class Player(Base):
    __tablename__ = "player"

    espn_id     = Column(Integer, primary_key=True)
    name        = Column(Text, nullable=False)
    dob         = Column(Text)
    nationality = Column(Text)
    height      = Column(Float)
    weight      = Column(Float)


# ── Game Info ─────────────────────────────────────────────────────────────────

class GameInfo(Base):
    __tablename__ = "game_info"

    espn_id     = Column(Integer, primary_key=True)
    date        = Column(Text, nullable=False)
    referee     = Column(Text)
    place       = Column(Text)
    state       = Column(Text)
    country     = Column(Text)
    commentary  = Column(JSONB)
    attendance  = Column(Integer)
    league_name = Column(Text)
    league_id   = Column(Text)

    team_histories = relationship("TeamGameHistory", back_populates="game")


# ── Team Game History ─────────────────────────────────────────────────────────

class TeamGameHistory(Base):
    __tablename__ = "team_game_history"

    id                = Column(Integer, primary_key=True)
    espn_team_id      = Column(Integer, ForeignKey("team.espn_id"), nullable=False)
    espn_game_info_id = Column(Integer, ForeignKey("game_info.espn_id"), nullable=False)
    formation         = Column(Text)
    goals             = Column(Integer, nullable=False)
    league_stats      = Column(JSONB)

    team              = relationship("Team", back_populates="game_histories")
    game              = relationship("GameInfo", back_populates="team_histories")
    goals_scored      = relationship("Goal", back_populates="team_game")
    fouls_committed   = relationship("Foul", back_populates="team_game")
    offsides          = relationship("Offside", back_populates="team_game")
    free_kicks        = relationship("FreeKick", back_populates="team_game")
    statistics        = relationship("TeamStatistics", back_populates="team_game", uselist=False)
    lineup            = relationship("LineUpStatistics", back_populates="team_game")


# ── Goals ─────────────────────────────────────────────────────────────────────

class Goal(Base):
    __tablename__ = "goals"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    espn_player_id      = Column(Integer, nullable=False)
    time                = Column(Text, nullable=False)
    own_goal            = Column(Boolean, nullable=False)

    team_game = relationship("TeamGameHistory", back_populates="goals_scored")


# ── Fouls ─────────────────────────────────────────────────────────────────────

class Foul(Base):
    __tablename__ = "fouls"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    espn_player_id      = Column(Integer, nullable=False)
    card_type           = Column(Text, nullable=False)
    time                = Column(Text, nullable=False)

    team_game = relationship("TeamGameHistory", back_populates="fouls_committed")


# ── Offside ───────────────────────────────────────────────────────────────────

class Offside(Base):
    __tablename__ = "offside"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    espn_player_id      = Column(Integer, nullable=False)
    time                = Column(Text, nullable=False)

    team_game = relationship("TeamGameHistory", back_populates="offsides")


# ── Free Kick ─────────────────────────────────────────────────────────────────

class FreeKick(Base):
    __tablename__ = "free_kick"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    time                = Column(Text, nullable=False)
    attacker_espn_id    = Column(Integer, nullable=False)
    attacker_style      = Column(Text, nullable=False)
    attacked_from       = Column(Text, nullable=False)
    saved_at            = Column(Text, nullable=False)

    team_game = relationship("TeamGameHistory", back_populates="free_kicks")


# ── Team Statistics ───────────────────────────────────────────────────────────

class TeamStatistics(Base):
    __tablename__ = "team_statistics"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    shot_on_goals       = Column(Integer)
    shot_attempts       = Column(Integer)
    fouls               = Column(Integer)
    goals               = Column(Integer)
    yellow_cards        = Column(Integer)
    red_cards           = Column(Integer)
    corner_kicks        = Column(Integer)
    saves               = Column(Integer)
    possession_percent  = Column(Float)

    team_game = relationship("TeamGameHistory", back_populates="statistics")


# ── Line Up Statistics ────────────────────────────────────────────────────────

class LineUpStatistics(Base):
    __tablename__ = "line_up_statistics"

    id                  = Column(Integer, primary_key=True)
    team_game_history_id = Column(Integer, ForeignKey("team_game_history.id"), nullable=False)
    espn_player_id      = Column(Integer, nullable=False)
    player_num          = Column(Integer)
    formation_position  = Column(Integer)
    goals               = Column(Integer)
    owngoals            = Column(Integer)
    saves               = Column(Integer)
    shots               = Column(Integer)
    shots_on_target     = Column(Integer)
    fouls_commited      = Column(Integer)
    fouls_suffered      = Column(Integer)
    assists             = Column(Integer)
    offsides            = Column(Integer)
    yellow_cards        = Column(Integer)
    red_cards           = Column(Integer)
    unused_player       = Column(Boolean)
    subbed_out_in_min   = Column(Integer)
    subbed_in_player    = Column(Integer)

    team_game = relationship("TeamGameHistory", back_populates="lineup")


# ── Tracker ───────────────────────────────────────────────────────────────────

class Tracker(Base):
    __tablename__ = "tracker"

    id               = Column(Integer, primary_key=True)
    scraped_team_url = Column(Text, nullable=False)
    scraped_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    status           = Column(Text, nullable=False)
    worker           = Column(Text, nullable=False, default="anonymous")


# ── Z Site: Executables Meta ──────────────────────────────────────────────────

class ZSiteExecutablesMeta(Base):
    __tablename__ = "z_site_executables_meta"

    id          = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name        = Column(Text, nullable=False)
    url         = Column(Text, nullable=False)
    description = Column(Text)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())


# ── Z Site: Sporty Fixtures ───────────────────────────────────────────────────

class ZSiteSportyFixtures(Base):
    __tablename__ = "z_site_sporty_fixtures"

    id               = Column(BigInteger, primary_key=True)
    tournament_name  = Column(Text, nullable=False)
    home_team        = Column(Text, nullable=False)
    home_team_logo   = Column(Text)
    away_team        = Column(Text, nullable=False)
    away_team_logo   = Column(Text)
    start_time       = Column(TIMESTAMP(timezone=True))
    sporty_match_id  = Column(Text)
    status           = Column(Text)
    markets          = Column(JSONB)
    scraped_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
