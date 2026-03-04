from contextlib import asynccontextmanager
import os
import shutil
import platform
import sys
from fastapi import FastAPI, Header, HTTPException,Request
from pathlib import Path
import subprocess

from db.database import engine
from models import orm
from routers import teams_players, games, events, statistics, admin
from routers.scraper_api import scraper_router


PROJECT_PATH = Path(__file__).resolve().parent.parent



def restart_service():
    system_name = platform.system()

    if system_name == "Linux":
        if shutil.which("systemctl"):
            subprocess.run(["systemctl", "restart", "espn_fastapi"], check=True)
    elif system_name == "Windows":
        python_exe = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        subprocess.Popen([python_exe, script_path])
        sys.exit(0)
    else:
        print(f"Restart not supported on {system_name}")

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
    print(f"Updating project at path: {PROJECT_PATH}")
    return {
        "status": "ok",
        "message": "GoalGraph API is running.",
        "docs": "/docs",
    }

@app.post("/update", tags=["Deployment"])
async def update_repo(request: Request, x_github_token: str = Header(None)):

        # Print request info
    print("=== Incoming Update Request ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Headers: {request.headers}")
    body = await request.body()
    print(f"Body: {body.decode('utf-8') if body else 'No body'}")
    print("==============================")

       
    print(f"Updating project at path: {PROJECT_PATH}")
    
    if x_github_token != os.getenv("GIT_SECRET_TOKEN"):
        raise HTTPException(status_code=403, detail="Forbidden")

    subprocess.run(["git", "fetch", "origin"], cwd=PROJECT_PATH)
    subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=PROJECT_PATH)

    # Restart FastAPI service (requires systemd setup)
    restart_service()

    return {"status": "updated and restarting"}
