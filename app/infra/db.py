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
        alert_sensitivity TEXT,
        welcome_message TEXT
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
        email_provider_id TEXT,
        report_content TEXT
    );
    
    CREATE TABLE IF NOT EXISTS action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        memory_source_hash TEXT NOT NULL,
        title TEXT NOT NULL,
        description_html TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, memory_source_hash)
    );
    """)
    conn.commit()
    
    try:
        c.execute("ALTER TABLE profiles ADD COLUMN welcome_message TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column likely already exists

    try:
        c.execute("ALTER TABLE report_history ADD COLUMN report_content TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column likely already exists
        
    conn.close()

if __name__ == "__main__":
    init_db()
