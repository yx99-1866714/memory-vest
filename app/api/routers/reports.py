from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from pydantic import BaseModel
from openai import OpenAI
from app.services.report_service import ReportService
from app.services.profile_service import ProfileService
from app.services.portfolio_service import PortfolioService
from app.services.memory_service import MemoryService
from app.services.market_data_service import MarketDataService
from app.services.news_service import NewsService
from app.config import settings

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"]
)

class ReportChatRequest(BaseModel):
    message: str
    report_content: str  # Raw report HTML passed from the frontend

def _get_llm_client():
    if not settings.openrouter_api_key:
        return None
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)


@router.get("/{user_id}")
def get_reports(user_id: str):
    """
    Fetch all historical reports generated for the user.
    """
    try:
        report_svc = ReportService()
        history = report_svc.get_user_reports(user_id)
        
        # Serialize the Pydantic models for JSON response
        return [h.model_dump() for h in history]
    except Exception as e:
        logging.error(f"Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/generate")
def generate_report(user_id: str):
    """
    On-demand generation of a new report for the user.
    """
    try:
        profile = ProfileService().get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=400, detail="User profile not found. Please log in first.")

        # Fetch stored action items and format as context for the report
        portfolio_svc = PortfolioService()
        positions = portfolio_svc.get_positions(user_id)
        cash = portfolio_svc.get_cash_balance(user_id)
        cash_amt = cash.available_cash if cash else 0.0
        stored_action_items = portfolio_svc.get_stored_action_items(user_id)
        if stored_action_items:
            action_items_context = "\n".join(
                f"- {item['title']} (created {item['created_at'][:10]})"
                for item in stored_action_items
            )
        else:
            action_items_context = "No active action items."

        memory_service = MemoryService()
        memory_context = memory_service.search_episodic_context(user_id)

        tickers = [p.ticker for p in positions]
        sectors = profile.sector_preferences
        market_data = MarketDataService().get_portfolio_market_context(tickers, sectors)
        news_data = NewsService().get_relevant_news(
            tickers=tickers,
            memory_context=memory_context,
            market_data=market_data
        )

        report_service = ReportService()
        report_text = report_service.generate_report(
            user_id=user_id,
            profile=profile.model_dump(mode='json'),
            positions=[p.model_dump(mode='json') for p in positions],
            cash=cash_amt,
            memory_context=memory_context,
            market_data=market_data,
            news_data=news_data,
            action_items_context=action_items_context
        )

        history_record = report_service.create_report_history_record(user_id, report_text)
        report_service.save_report_history(history_record)

        return history_record.model_dump()
    except Exception as e:
        logging.error(f"Error generating report manually: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{report_id}")
def delete_report(user_id: str, report_id: str):
    """
    Delete a specific report by report_id.
    """
    try:
        report_svc = ReportService()
        deleted = report_svc.delete_report(user_id, report_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Report not found.")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/{report_id}/email")
def email_report(user_id: str, report_id: str):
    """
    Sends the specified report to the user's registered email address.
    """
    try:
        profile = ProfileService().get_profile(user_id)
        if not profile or not profile.email:
            raise HTTPException(status_code=400, detail="No email address found for this user. Please set your email in Settings.")

        report_svc = ReportService()
        reports = report_svc.get_user_reports(user_id)
        report = next((r for r in reports if r.report_id == report_id), None)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        if not report.report_content:
            raise HTTPException(status_code=400, detail="This report has no content to send.")

        report_svc.send_report_email(
            to_email=profile.email,
            report_content=report.report_content,
            generated_at=report.generated_at.isoformat()
        )
        return {"success": True, "sent_to": profile.email}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error emailing report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.get("/{user_id}/{report_id}/chat-welcome")
def report_chat_welcome(user_id: str, report_id: str):
    """
    Returns an AI welcome message inviting the user to discuss the selected report.
    """
    try:
        client = _get_llm_client()
        if not client:
            return {"message": "Hi! Feel free to ask me questions about this report, or tell me how you'd like future reports to be tailored for you."}

        profile = ProfileService().get_profile(user_id)
        name_hint = f" {profile.email.split('@')[0]}" if profile and profile.email else ""

        welcome_prompt = (
            f"You are MemoryVest, a friendly and beginner-friendly investing assistant. "
            f"The user{name_hint} has just opened their portfolio report. "
            f"Send them a warm, concise welcome message (2-3 sentences max) inviting them to: "
            f"(1) ask any questions about the report's contents, or "
            f"(2) share feedback so you can tailor future reports better. "
            f"Be conversational and encouraging, not formal."
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": welcome_prompt}],
            temperature=0.7,
            max_tokens=120
        )
        return {"message": response.choices[0].message.content.strip()}
    except Exception as e:
        logging.error(f"Report chat welcome error: {e}")
        return {"message": "Hi! Feel free to ask me questions about this report, or share any feedback on how you'd like future reports to look."}

@router.post("/{user_id}/chat")
def report_chat(user_id: str, request: ReportChatRequest):
    """
    Chat endpoint that uses the current report as context for the AI response.
    Also stores feedback/preferences into EverMemOS.
    """
    try:
        client = _get_llm_client()
        if not client:
            raise HTTPException(status_code=503, detail="LLM not configured.")

        profile = ProfileService().get_profile(user_id)
        profile_hint = f"User profile: {profile.model_dump(mode='json')}" if profile else ""

        system_prompt = (
            "You are MemoryVest, a friendly and beginner-friendly investing assistant. "
            "The user is discussing a report that was just generated for them. "
            "Answer their questions about the report clearly and simply. "
            "If they provide feedback or preferences (e.g. 'make reports shorter', 'focus more on tech'), "
            "acknowledge it warmly and confirm you'll remember it. "
            "Keep responses concise (3-5 sentences max)."
        )

        user_prompt = (
            f"{profile_hint}\n\n"
            f"REPORT CONTENT (HTML, use for context only):\n{request.report_content[:4000]}\n\n"
            f"USER MESSAGE: {request.message}"
        )

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=250
        )
        reply = response.choices[0].message.content.strip()

        # Store feedback/preference in EverMemOS so it influences future reports
        try:
            MemoryService().store_user_message(user_id=user_id, content=f"Report feedback: {request.message}")
        except Exception as me:
            logging.warning(f"Failed to store report feedback in EverMemOS: {me}")

        return {"reply": reply}
    except Exception as e:
        logging.error(f"Report chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
