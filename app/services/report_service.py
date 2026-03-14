import json
from openai import OpenAI
from pathlib import Path
from datetime import datetime, timezone
import uuid
from app.config import settings
from app.models.report import ReportHistory
from app.infra.db import get_db_connection
import logging

class ReportService:
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
            
        prompt_path = Path(__file__).parent.parent / "prompts" / "generate_daily_report.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def generate_report(self, user_id: str, profile: dict, positions: list, cash: float, memory_context: str, market_data: dict, news_data: list) -> str:
        """
        Generates the daily report string using LLM.
        """
        if not self.client:
            logging.warning("OPENROUTER_API_KEY is not set. Using fallback mock report.")
            return "Mock Report generated because OpenRouter key is missing."

        prompt = self.prompt_template.format(
            profile_json=json.dumps(profile, indent=2),
            portfolio_json=json.dumps(positions, indent=2),
            cash_balance=cash,
            memory_context=memory_context,
            market_data_json=json.dumps(market_data, indent=2),
            news_json=json.dumps(news_data, indent=2)
        )

        try:
            logging.debug(f"Report LLM model used: {self.model}")
            logging.debug(f"Report LLM prompt: \n{prompt}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a personalized, beginner-friendly investing assistant. Read the system prompt carefully."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            report_text = response.choices[0].message.content.strip()
            logging.debug(f"Report LLM Response: \n{report_text}")
            return report_text
        except Exception as e:
            logging.error(f"Error calling LLM for report: {e}")
            return "There was an error generating your request today. Please try again later."
            
    def create_report_history_record(self, user_id: str, report_text: str) -> ReportHistory:
        return ReportHistory(
            report_id=f"rpt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}",
            user_id=user_id,
            generated_at=datetime.now(timezone.utc),
            delivery_status="generated",
            headline_topics=[],
            mentioned_tickers=[],
            email_provider_id="none",
            report_content=report_text
        )

    def save_report_history(self, report: ReportHistory):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO report_history (
                report_id, user_id, generated_at, delivery_status,
                headline_topics, mentioned_tickers, email_provider_id, report_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.report_id, report.user_id, report.generated_at.isoformat(),
                report.delivery_status, json.dumps(report.headline_topics),
                json.dumps(report.mentioned_tickers), report.email_provider_id,
                report.report_content
            )
        )
        conn.commit()
        conn.close()

    def get_user_reports(self, user_id: str) -> list[ReportHistory]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM report_history WHERE user_id = ? ORDER BY generated_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            d = dict(row)
            d["headline_topics"] = json.loads(d["headline_topics"])
            d["mentioned_tickers"] = json.loads(d["mentioned_tickers"])
            results.append(ReportHistory(**d))
            
        return results
