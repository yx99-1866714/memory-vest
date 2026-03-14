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

    def generate_action_items(self, profile: dict, positions: list, market_data: dict, memory_context: str = "") -> str:
        """Generates a contextual watchlist of 3-4 action items."""
        if not self.client:
           return "<p><i>API key is missing. Cannot generate Action Items.</i></p>"
           
        prompt = self.action_items_prompt_template.format(
            profile_json=json.dumps(profile, indent=2),
            portfolio_json=json.dumps(positions, indent=2),
            market_data_json=json.dumps(market_data, indent=2),
            memory_context=memory_context if memory_context else "None"
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

    def generate_single_action_item_html(self, directive: str, profile: dict, positions: list, market_data: dict) -> str:
        """Generates a single collapsible <details> action item for a specific user directive."""
        if not self.client:
            return ""
        single_prompt = f"""You are MemoryVest, a beginner-friendly investing assistant.
Generate a SINGLE collapsible HTML action item for the following user directive.

Directive: "{directive}"

User Profile: {json.dumps(profile)}
Portfolio: {json.dumps(positions)}
Market Context: {json.dumps(market_data)}

Output ONLY a single <details> element. The <summary> must be a short title (5-7 words max).
The inner <p> must be ONE concise sentence restating what the task is. Do NOT include market analysis or stock prices.

Example:
<details>
  <summary>Monitor Iran Conflict Impact on Energy</summary>
  <p>Based on your request to closely watch the ongoing conflict in Iran and monitor its impact on your holdings and the sectors you care about.</p>
</details>"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise HTML generator. Output only the requested HTML."},
                    {"role": "user", "content": single_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Single Action Item LLM Error: {e}")
            return ""

    def deduplicate_new_directives(self, new_directives: list[str], existing_titles: list[str]) -> list[str]:
        """
        Uses the LLM to compare new_directives against existing_titles and returns only 
        those that represent a genuinely novel topic not yet covered by any existing item.
        """
        if not new_directives:
            return []
        # If there are no existing items yet, only deduplicate within the new batch itself
        dedup_prompt = f"""You are a deduplication assistant.

You have a list of NEW user directives from a chat history, and a list of EXISTING action item titles that have already been generated.

Your job is:
1. Remove any NEW directive that covers the SAME topic as an existing title (semantically, not just word-for-word).
2. From the remaining new directives, if multiple cover the SAME topic as each other, keep only ONE representative directive (the most descriptive one).
3. Return ONLY the deduplicated list of new directives as a JSON array of strings. Nothing else.

EXISTING action item titles (already generated, skip any new directive that matches these):
{json.dumps(existing_titles)}

NEW directives to evaluate:
{json.dumps(new_directives)}

Output format: ["directive 1", "directive 2", ...]
If nothing is novel, output: []"""

        if not self.client:
            # Without LLM, just return unique directives not covered by existing (basic substring check)
            lowered_existing = [t.lower() for t in existing_titles]
            seen_stems = set()
            result = []
            for d in new_directives:
                d_lower = d.lower()
                key_words = set(d_lower.split())
                if any(kw in ' '.join(lowered_existing) for kw in key_words if len(kw) > 4):
                    continue
                stem = d_lower[:30]
                if stem not in seen_stems:
                    seen_stems.add(stem)
                    result.append(d)
            return result

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise JSON deduplication assistant. Output only valid JSON."},
                    {"role": "user", "content": dedup_prompt}
                ],
                temperature=0.0
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            return json.loads(raw)
        except Exception as e:
            logging.error(f"Dedup LLM error: {e}")
            # Fallback: return all new directives unfiltered rather than dropping them
            return new_directives

    # ---- Persistent Action Items DB CRUD ----

    def get_stored_action_items(self, user_id: str) -> list:
        """Returns all stored action items for a user from the database."""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT id, memory_source_hash, title, description_html, created_at FROM action_items WHERE user_id = ? ORDER BY created_at ASC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def save_action_item(self, user_id: str, memory_source_hash: str, title: str, description_html: str) -> bool:
        """Inserts a new action item. Returns True if inserted, False if it already exists."""
        conn = get_db_connection()
        try:
            from datetime import datetime, timezone
            conn.execute(
                "INSERT OR IGNORE INTO action_items (user_id, memory_source_hash, title, description_html, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, memory_source_hash, title, description_html, datetime.now(timezone.utc).isoformat())
            )
            inserted = conn.total_changes > 0
            conn.commit()
            return inserted
        finally:
            conn.close()

    def get_existing_hashes(self, user_id: str) -> set:
        """Returns the set of memory_source_hashes already stored for a user."""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT memory_source_hash FROM action_items WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            return {r["memory_source_hash"] for r in rows}
        finally:
            conn.close()

    def delete_action_item(self, user_id: str, item_id: int) -> bool:
        """Deletes a specific action item by its internal DB id."""
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM action_items WHERE id = ? AND user_id = ?", (item_id, user_id))
            conn.commit()
            return conn.total_changes > 0
        finally:
            conn.close()
