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

        positions = PortfolioService().get_positions(user_id)
        cash = PortfolioService().get_cash_balance(user_id)
        cash_amt = cash.available_cash if cash else 0.0

        memory_service = MemoryService()
        memory_context = memory_service.search_episodic_context(user_id)

        tickers = [p.ticker for p in positions]
        sectors = profile.sector_preferences
        market_data = MarketDataService().get_portfolio_market_context(tickers, sectors)
        news_data = NewsService().get_relevant_news(profile.interests, tickers)

        report_service = ReportService()
        report_text = report_service.generate_report(
            user_id=user_id,
            profile=profile.model_dump(mode='json'),
            positions=[p.model_dump(mode='json') for p in positions],
            cash=cash_amt,
            memory_context=memory_context,
            market_data=market_data,
            news_data=news_data
        )

        history_record = report_service.create_report_history_record(user_id, report_text)
        report_service.save_report_history(history_record)

        return history_record.model_dump()
    except Exception as e:
        logging.error(f"Error generating report manually: {e}")
        raise HTTPException(status_code=500, detail=str(e))
