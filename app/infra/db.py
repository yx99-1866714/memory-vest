import sqlite3
import json
from pathlib import Path
from app.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.executescript("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id TEXT PRIMARY KEY,
        email TEXT,
        experience_level TEXT,
        risk_tolerance TEXT,
        explanation_style TEXT,
        jargon_tolerance TEXT,
        report_frequency TEXT,
        report_length TEXT,
        timezone TEXT,
        interests TEXT,
        sector_preferences TEXT,
        alert_sensitivity TEXT
    );
    
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        ticker TEXT,
        shares REAL,
        avg_cost REAL,
        opened_at TEXT,
        status TEXT
    );
    
    CREATE TABLE IF NOT EXISTS cash_balances (
        user_id TEXT PRIMARY KEY,
        available_cash REAL,
        currency TEXT,
        updated_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS watch_intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        ticker TEXT,
        type TEXT,
        note TEXT,
        target_zone_low REAL,
        target_zone_high REAL,
        status TEXT
    );
    
    CREATE TABLE IF NOT EXISTS report_history (
        report_id TEXT PRIMARY KEY,
        user_id TEXT,
        generated_at TEXT,
        delivery_status TEXT,
        headline_topics TEXT,
        mentioned_tickers TEXT,
        email_provider_id TEXT
    );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
