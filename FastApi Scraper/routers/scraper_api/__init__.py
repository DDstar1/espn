from fastapi import APIRouter
from routers.scraper_api import (
    players,
    teams,
    game_info,
    team_game_history,
    team_statistics,
    lineup_statistics,
    events,
    tracker,
)

# Single router that all scraper sub-routers attach to.
# Mounted at /scraper in main.py
scraper_router = APIRouter(prefix="/scraper")

scraper_router.include_router(players.router)
scraper_router.include_router(teams.router)
scraper_router.include_router(game_info.router)
scraper_router.include_router(team_game_history.router)
scraper_router.include_router(team_statistics.router)
scraper_router.include_router(lineup_statistics.router)
scraper_router.include_router(events.router)
scraper_router.include_router(tracker.router)
