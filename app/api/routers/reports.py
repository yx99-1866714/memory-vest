from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from app.services.report_service import ReportService
from app.services.profile_service import ProfileService
from app.services.portfolio_service import PortfolioService
from app.services.memory_service import MemoryService
from app.services.market_data_service import MarketDataService
from app.services.news_service import NewsService

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"]
)

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
