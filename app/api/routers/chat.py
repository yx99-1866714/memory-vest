from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService
from app.services.profile_service import ProfileService
from app.services.portfolio_service import PortfolioService
from app.models.profile import UserProfile
from app.models.position import Position, CashBalance

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)

class ChatRequest(BaseModel):
    message: str

@router.get("/welcome/{user_id}")
def get_welcome_message(user_id: str):
    try:
        profile_svc = ProfileService()
        portfolio_svc = PortfolioService()
        memory_svc = MemoryService()
        extractor = ExtractionService()
        
        current_profile = profile_svc.get_profile(user_id)
        if not current_profile:
             return {"message": "Hi, I'm MemoryVest, your companion agent for investing. Feel free to talk to me anytime you want. You can tell me things like your interests/hobbies, experience levels, risk tolerances, what stocks to watch for, etc. and I will generate regular reports for you and send them to your email."}
             
        if current_profile.welcome_message:
            msg = current_profile.welcome_message
            current_profile.welcome_message = None
            profile_svc.upsert_profile(current_profile)
            return {"message": msg}
            
        current_positions = portfolio_svc.get_positions(user_id)
        memory_context = memory_svc.search_episodic_context(user_id)
        welcome_msg = extractor.generate_welcome_message(current_profile, current_positions, memory_context)
        return {"message": welcome_msg}
    except Exception as e:
        logging.error(f"Error generating welcome message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}")
def process_chat(user_id: str, request: ChatRequest):
    try:
        user_input = request.message
        extractor = ExtractionService()
        memory_svc = MemoryService()
        profile_svc = ProfileService()
        portfolio_svc = PortfolioService()
        
        current_profile = profile_svc.get_profile(user_id)
        current_positions = portfolio_svc.get_positions(user_id)
        current_cash_bal = portfolio_svc.get_cash_balance(user_id)
        cash_amt = current_cash_bal.available_cash if current_cash_bal else 0.0

        extracted = extractor.parse_user_input(
            user_input=user_input, 
            current_profile=current_profile, 
            current_positions=current_positions, 
            current_cash=cash_amt
        )
        
        # Apply Profile Updates
        profile_updates = extracted.get("profile_updates", {})
        if profile_updates and any(v is not None for v in profile_updates.values()):
            if current_profile:
                for k, v in profile_updates.items():
                    if v is not None and hasattr(current_profile, k):
                        setattr(current_profile, k, v)
                profile_svc.upsert_profile(current_profile)
            else:
                new_profile = UserProfile(
                    user_id=user_id,
                    email=profile_updates.get("email") or "demo@example.com",
                    experience_level=profile_updates.get("experience_level") or "beginner",
                    risk_tolerance=profile_updates.get("risk_tolerance") or "moderate",
                    explanation_style=profile_updates.get("explanation_style") or "plain_english",
                    jargon_tolerance=profile_updates.get("jargon_tolerance") or "low",
                    report_frequency=profile_updates.get("report_frequency") or "daily",
                    report_length=profile_updates.get("report_length") or "short",
                    timezone=profile_updates.get("timezone") or "UTC",
                    interests=profile_updates.get("interests") or [],
                    sector_preferences=profile_updates.get("sector_preferences") or [],
                    alert_sensitivity=profile_updates.get("alert_sensitivity") or "important_only"
                )
                profile_svc.upsert_profile(new_profile)

        # Apply Portfolio Additions
        for p in extracted.get("positions_to_add", []):
            try:
                pos = Position(
                    user_id=user_id,
                    ticker=p.get("ticker", "").upper(),
                    shares=float(p.get("shares", 0.0)),
                    avg_cost=float(p.get("avg_cost", 0.0)),
                    opened_at=datetime.utcnow(),
                    status="open"
                )
                portfolio_svc.add_position(pos)
            except Exception as pe:
                logging.error(f"Failed parsing position: {pe}")

        # Update Cash
        if extracted.get("cash_update") is not None:
            bal = CashBalance(
                user_id=user_id,
                available_cash=float(extracted["cash_update"]),
                updated_at=datetime.utcnow()
            )
            portfolio_svc.upsert_cash_balance(bal)

        # Record Context Note to Memory
        memory_note = extracted.get("memory_note")
        watch_intents = extracted.get("watch_intents")
        
        if memory_note or watch_intents:
            try:
                # Store the literal user request so foresight/episodic retrieval can find it
                memory_svc.store_user_message(user_id=user_id, content=user_input)
            except Exception as me:
                 logging.error(f"EverMemOS error: {me}")

        response_msg = extracted.get("response_message")
        reply = response_msg if response_msg else (memory_note if memory_note else "I've noted your input and updated your profile/portfolio accordingly.")
        return {"reply": reply, "extracted": extracted}

    except Exception as e:
        logging.error(f"Error processing chat POST: {e}")
        raise HTTPException(status_code=500, detail=str(e))
