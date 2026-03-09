from pydantic import BaseModel
from datetime import datetime

class Position(BaseModel):
    user_id: str
    ticker: str
    shares: float
    avg_cost: float
    opened_at: datetime
    status: str

class CashBalance(BaseModel):
    user_id: str
    available_cash: float
    currency: str = "USD"
    updated_at: datetime
