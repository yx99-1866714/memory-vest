from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from app.config import settings
from app.api.routers import market, profile, chat, portfolio, auth, reports

# Configure Application Logging
log_level = logging.DEBUG if settings.verbose_mode else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the DB directory exists (important when using a Render persistent disk)
    db_dir = Path(settings.db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    from app.infra.db import init_db
    init_db()
    logger.info(f"Database initialised at {settings.db_path}")
    yield

app = FastAPI(title="MemoryVest Dedicated Market API", lifespan=lifespan)

# Setup CORS to allow the Vite frontend (which usually runs on localhost:5173) requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular routers
app.include_router(auth.router)
app.include_router(market.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(portfolio.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    logger.debug("Root endpoint accessed.")
    return {"message": "MemoryVest Dedicated API running."}
