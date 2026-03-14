from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routers import market, profile, chat, portfolio, auth, reports

app = FastAPI(title="MemoryVest Dedicated Market API")

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
    return {"message": "MemoryVest Dedicated API running."}
