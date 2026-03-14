from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.profile_service import ProfileService

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

class LoginRequest(BaseModel):
    email: str

@router.post("/login")
async def login(request: LoginRequest):
    email = request.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    try:
        profile_svc = ProfileService()
        user_id = profile_svc.get_or_create_user_by_email(email)
        return {"user_id": user_id, "status": "success"}
    except Exception as e:
        logging.error(f"Error logging in: {e}")
        raise HTTPException(status_code=500, detail=str(e))
