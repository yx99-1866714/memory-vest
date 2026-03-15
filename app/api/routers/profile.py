from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.profile_service import ProfileService
from app.models.profile import UserProfile

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"]
)

class ProfileUpdateRequest(BaseModel):
    email: str | None = None
    experience_level: str | None = None
    risk_tolerance: str | None = None
    interests: str | None = None
    report_frequency: str | None = None

@router.get("/{user_id}")
async def get_profile(user_id: str):
    try:
        profile_svc = ProfileService()
        profile = profile_svc.get_profile(user_id)
        if not profile:
            return {
                "email": "user@example.com",
                "experienceLevel": "beginner",
                "riskTolerance": "moderate",
                "interests": "AI, Clean Energy, Web3",
                "reportFrequency": "daily"
            }
        
        return {
            "email": profile.email,
            "experienceLevel": profile.experience_level,
            "riskTolerance": profile.risk_tolerance,
            "interests": ", ".join(profile.interests) if profile.interests else "",
            "reportFrequency": profile.report_frequency
        }
    except Exception as e:
        logging.error(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}")
async def update_profile(user_id: str, request: ProfileUpdateRequest):
    try:
        profile_svc = ProfileService()
        profile = profile_svc.get_profile(user_id)
        
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                email=request.email or "demo@example.com",
                experience_level=request.experience_level or "beginner",
                risk_tolerance=request.risk_tolerance or "moderate",
                explanation_style="plain_english",
                jargon_tolerance="low",
                report_frequency=request.report_frequency or "daily",
                report_length="short",
                timezone="UTC",
                interests=[i.strip() for i in request.interests.split(",") if i.strip()] if request.interests else [],
                sector_preferences=[],
                alert_sensitivity="important_only"
            )
        else:
            if request.email: profile.email = request.email
            if request.experience_level: profile.experience_level = request.experience_level
            if request.risk_tolerance: profile.risk_tolerance = request.risk_tolerance
            if request.report_frequency: profile.report_frequency = request.report_frequency
            if request.interests is not None:
                profile.interests = [i.strip() for i in request.interests.split(",") if i.strip()]
                
        profile_svc.upsert_profile(profile)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
def delete_user(user_id: str):
    """
    Permanently deletes the user and all their data.
    Order: EverMemOS memories first, then local DB (all tables).
    """
    from app.infra.evermemos_client import EverMemOSClient
    from app.infra.db import get_db_connection

    errors = []

    # 1 — Delete EverMemOS memories (best-effort, don't block DB wipe on failure)
    try:
        EverMemOSClient().delete_all_user_memories(user_id)
        logging.info(f"EverMemOS memories deleted for user {user_id}")
    except Exception as e:
        logging.warning(f"EverMemOS deletion failed (continuing): {e}")
        errors.append(f"EverMemOS: {e}")

    # 2 — Wipe all local DB tables
    try:
        conn = get_db_connection()
        c = conn.cursor()
        tables = ["profiles", "positions", "cash_balances", "watch_intents", "report_history", "action_items"]
        for table in tables:
            c.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        # Also wipe auth record if it exists
        try:
            c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        except Exception:
            pass  # Table may not exist
        conn.commit()
        conn.close()
        logging.info(f"All local DB data deleted for user {user_id}")
    except Exception as e:
        logging.error(f"DB deletion failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete local data: {e}")

    return {"success": True, "warnings": errors}

