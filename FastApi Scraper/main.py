from contextlib import asynccontextmanager
from fastapi import FastAPI

from db.database import engine
from models import orm  # ensures all ORM models are registered
from routers import teams_players, games, events, statistics, admin
from routers.scraper_api import scraper_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Nothing to do on startup beyond letting SQLAlchemy manage the pool.
    # If you want to auto-create tables during development, uncomment:
    #
    #   async with engine.begin() as conn:
    #       await conn.run_sync(orm.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="GoalGraph API",
    description="Football match data, statistics, and scraping tracker.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(teams_players.router, tags=["Teams & Players"])
app.include_router(games.router,         tags=["Games"])
app.include_router(events.router,        tags=["Match Events"])
app.include_router(statistics.router,    tags=["Statistics"])
app.include_router(admin.router,         tags=["Admin / Site Data"])
app.include_router(scraper_router,       tags=["Scraper API"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "message": "GoalGraph API is running.",
        "docs": "/docs",
    }
