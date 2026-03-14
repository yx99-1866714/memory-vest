from pydantic import BaseModel
from typing import List
from datetime import datetime

class ReportHistory(BaseModel):
    report_id: str
    user_id: str
    generated_at: datetime
    delivery_status: str
    headline_topics: List[str]
    mentioned_tickers: List[str]
    email_provider_id: str
    report_content: str = ""
