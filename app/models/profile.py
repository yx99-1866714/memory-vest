from pydantic import BaseModel, EmailStr
from typing import List

class UserProfile(BaseModel):
    user_id: str
    email: EmailStr
    experience_level: str
    risk_tolerance: str
    explanation_style: str
    jargon_tolerance: str
    report_frequency: str
    report_length: str
    timezone: str
    interests: List[str]
    sector_preferences: List[str]
    alert_sensitivity: str
