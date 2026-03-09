import json
from typing import Optional
from app.models.profile import UserProfile
from app.infra.db import get_db_connection

class ProfileService:
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            d = dict(row)
            d["interests"] = json.loads(d["interests"])
            d["sector_preferences"] = json.loads(d["sector_preferences"])
            return UserProfile(**d)
        return None

    def upsert_profile(self, profile: UserProfile):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO profiles (
                user_id, email, experience_level, risk_tolerance,
                explanation_style, jargon_tolerance, report_frequency,
                report_length, timezone, interests, sector_preferences,
                alert_sensitivity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email=excluded.email,
                experience_level=excluded.experience_level,
                risk_tolerance=excluded.risk_tolerance,
                explanation_style=excluded.explanation_style,
                jargon_tolerance=excluded.jargon_tolerance,
                report_frequency=excluded.report_frequency,
                report_length=excluded.report_length,
                timezone=excluded.timezone,
                interests=excluded.interests,
                sector_preferences=excluded.sector_preferences,
                alert_sensitivity=excluded.alert_sensitivity
            """,
            (
                profile.user_id, profile.email, profile.experience_level,
                profile.risk_tolerance, profile.explanation_style, profile.jargon_tolerance,
                profile.report_frequency, profile.report_length, profile.timezone,
                json.dumps(profile.interests), json.dumps(profile.sector_preferences),
                profile.alert_sensitivity
            )
        )
        conn.commit()
        conn.close()
