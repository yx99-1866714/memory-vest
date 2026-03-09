import os
import sys

# Ensure the app imports work regardless of where script is run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.infra.db import init_db
from app.services.profile_service import ProfileService
from app.models.profile import UserProfile
from app.services.portfolio_service import PortfolioService
from app.models.position import Position, CashBalance
from datetime import datetime
import subprocess

print("=========================================")
print("   MemoryVest MVP Demo Script ")
print("=========================================")
print("")
print("1. Initializing the Database...")
init_db()

print("")
print("=========================================")
print("2. Spawning Mock User State")
print("=========================================")

pf_svc = ProfileService()
pf_svc.upsert_profile(UserProfile(
    user_id='user_001',
    email='demo@example.com',
    experience_level='beginner',
    risk_tolerance='low',
    explanation_style='plain_english',
    jargon_tolerance='low',
    report_frequency='daily',
    report_length='short',
    timezone='UTC',
    interests=['AI', 'gaming'],
    sector_preferences=['technology'],
    alert_sensitivity='high'
))

pt_svc = PortfolioService()
pt_svc.add_position(Position(
    user_id='user_001',
    ticker='AAPL',
    shares=10.0,
    avg_cost=150.0,
    opened_at=datetime.utcnow(),
    status='open'
))

pt_svc.upsert_cash_balance(CashBalance(
    user_id='user_001',
    available_cash=5000.0,
    currency='USD',
    updated_at=datetime.utcnow()
))

print("State seeded!")
print("")
print("=========================================")
print("3. Generating Report Preview")
print("=========================================")

subprocess.run(["uv", "run", "memoryvest", "report", "preview", "--user-id", "user_001"])

print("")
print("Demo complete!")
