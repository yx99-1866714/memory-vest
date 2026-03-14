import json
from typing import List, Optional
from pathlib import Path
from openai import OpenAI
import logging
from app.models.position import Position, CashBalance
from app.infra.db import get_db_connection
from app.config import settings

class PortfolioService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.llm_model
        if self.api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        else:
            self.client = None
            
        prompt_path = Path(__file__).parent.parent / "prompts" / "portfolio_review.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.review_prompt_template = f.read()
            
        action_items_prompt_path = Path(__file__).parent.parent / "prompts" / "action_items_prompt.txt"
        with open(action_items_prompt_path, "r", encoding="utf-8") as f:
            self.action_items_prompt_template = f.read()

    def get_positions(self, user_id: str) -> List[Position]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM positions WHERE user_id = ? AND status = 'open'", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        return [Position(**dict(row)) for row in rows]

    def add_position(self, position: Position):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO positions (user_id, ticker, shares, avg_cost, opened_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (position.user_id, position.ticker, position.shares, position.avg_cost, position.opened_at.isoformat(), position.status)
        )
        conn.commit()
        conn.close()
        
    def remove_position(self, user_id: str, ticker: str):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE positions SET status = 'closed' WHERE user_id = ? AND ticker = ? AND status = 'open'", (user_id, ticker))
        conn.commit()
        conn.close()

    def clear_portfolio(self, user_id: str):
        conn = get_db_connection()
        c = conn.cursor()
        # For a true overwrite, we soft-delete everything open
        c.execute("UPDATE positions SET status = 'closed' WHERE user_id = ? AND status = 'open'", (user_id,))
        conn.commit()
        conn.close()
    
    def get_cash_balance(self, user_id: str) -> Optional[CashBalance]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM cash_balances WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return CashBalance(**dict(row))
        return None

    def upsert_cash_balance(self, balance: CashBalance):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO cash_balances (user_id, available_cash, currency, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                available_cash=excluded.available_cash,
                currency=excluded.currency,
                updated_at=excluded.updated_at
            """,
            (balance.user_id, balance.available_cash, balance.currency, balance.updated_at.isoformat())
        )
        conn.commit()
        conn.close()

    def generate_ai_review(self, profile: dict, positions: list, market_data: dict) -> str:
        """Generates a concise 2-paragraph HTML review of the portfolio."""
        if not self.client:
           return "<p><i>API key is missing. Cannot generate AI Review.</i></p>"
           
        prompt = self.review_prompt_template.format(
            profile_json=json.dumps(profile, indent=2),
            portfolio_json=json.dumps(positions, indent=2),
            market_data_json=json.dumps(market_data, indent=2),
            risk_tolerance=profile.get('risk_tolerance', 'undefined'),
            experience_level=profile.get('experience_level', 'undefined')
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise portfolio analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Portfolio Review LLM Error: {e}")
            return "<p>Failed to generate portfolio review at this time.</p>"

    def generate_action_items(self, profile: dict, positions: list, market_data: dict) -> str:
        """Generates a contextual watchlist of 3-4 action items."""
        if not self.client:
           return "<p><i>API key is missing. Cannot generate Action Items.</i></p>"
           
        prompt = self.action_items_prompt_template.format(
            profile_json=json.dumps(profile, indent=2),
            portfolio_json=json.dumps(positions, indent=2),
            market_data_json=json.dumps(market_data, indent=2)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise portfolio analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Action Items LLM Error: {e}")
            return "<p>Failed to generate action items at this time.</p>"
