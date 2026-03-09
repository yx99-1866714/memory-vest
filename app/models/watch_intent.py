from pydantic import BaseModel
from typing import Optional

class WatchIntent(BaseModel):
    user_id: str
    ticker: str
    type: str # e.g. "price_watch"
    note: str
    target_zone_low: Optional[float] = None
    target_zone_high: Optional[float] = None
    status: str = "active"
