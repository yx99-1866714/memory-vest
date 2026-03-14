from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import List
import logging
from datetime import datetime

from app.services.portfolio_service import PortfolioService
from app.services.extraction_service import ExtractionService
from app.services.profile_service import ProfileService
from app.services.market_data_service import MarketDataService
from app.models.position import Position

router = APIRouter(
    prefix="/api/portfolio",
    tags=["portfolio"]
)

class PositionCreateUpdate(BaseModel):
    ticker: str
    shares: float
    avg_cost: float

class PositionsBulkImport(BaseModel):
    positions: List[PositionCreateUpdate]

class CashUpdate(BaseModel):
    available_cash: float

@router.get("/{user_id}/positions")
async def get_positions(user_id: str):
    try:
        portfolio_svc = PortfolioService()
        positions = portfolio_svc.get_positions(user_id)
        # Format for React frontend
        formatted = [
            {
                "id": pos.ticker, # using ticker as stable unique ID locally for frontend MVP
                "ticker": pos.ticker,
                "shares": pos.shares,
                "avgCost": pos.avg_cost,
                "currentPrice": None # To be hydrated dynamically
            } for pos in positions
        ]
        return formatted
    except Exception as e:
        logging.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/cash")
async def get_cash(user_id: str):
    try:
        portfolio_svc = PortfolioService()
        balance = portfolio_svc.get_cash_balance(user_id)
        if balance:
            return {"available_cash": balance.available_cash}
        return {"available_cash": 0.0} # Default fallback
    except Exception as e:
        logging.error(f"Error fetching cash balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/review")
def get_portfolio_review(user_id: str):
    """
    On-demand AI review of the current portfolio.
    """
    try:
        portfolio_svc = PortfolioService()
        positions = portfolio_svc.get_positions(user_id)
        if not positions:
             return {"review": "<p>You don't have any holdings yet! Add a position manually or import a CSV to get an AI review.</p>"}
             
        profile = ProfileService().get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found.")
            
        tickers = [p.ticker for p in positions]
        market_data = MarketDataService().get_portfolio_market_context(tickers, profile.sector_preferences)
        
        review_html = portfolio_svc.generate_ai_review(
            profile=profile.model_dump(mode='json'),
            positions=[p.model_dump(mode='json') for p in positions],
            market_data=market_data
        )
        return {"review": review_html}
    except Exception as e:
        logging.error(f"Error generating AI portfolio review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/action-items")
def get_action_items(user_id: str):
    """
    On-demand AI watchlist based on the current portfolio.
    """
    try:
        portfolio_svc = PortfolioService()
        positions = portfolio_svc.get_positions(user_id)
        if not positions:
             return {"action_items": "<p>You don't have any holdings yet! Add a position manually or import a CSV to unlock tailored Action Items.</p>"}
             
        profile = ProfileService().get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=400, detail="Profile not found.")
            
        tickers = [p.ticker for p in positions]
        market_data = MarketDataService().get_portfolio_market_context(tickers, profile.sector_preferences)
        
        action_items_html = portfolio_svc.generate_action_items(
            profile=profile.model_dump(mode='json'),
            positions=[p.model_dump(mode='json') for p in positions],
            market_data=market_data
        )
        return {"action_items": action_items_html}
    except Exception as e:
        logging.error(f"Error generating AI action items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/cash")
async def update_cash(user_id: str, request: CashUpdate):
    try:
        from app.models.position import CashBalance
        portfolio_svc = PortfolioService()
        
        balance = CashBalance(
            user_id=user_id,
            available_cash=request.available_cash,
            updated_at=datetime.utcnow()
        )
        portfolio_svc.upsert_cash_balance(balance)
        return {"status": "success", "available_cash": balance.available_cash}
    except Exception as e:
        logging.error(f"Error updating cash balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/positions")
async def add_position(user_id: str, request: PositionCreateUpdate):
    try:
        portfolio_svc = PortfolioService()
        pos = Position(
            user_id=user_id,
            ticker=request.ticker.upper(),
            shares=request.shares,
            avg_cost=request.avg_cost,
            opened_at=datetime.utcnow(),
            status="open"
        )
        # add_position in PortfolioService essentially acts as upsert based on DB schema constraints
        portfolio_svc.add_position(pos)
        return {"status": "success", "ticker": pos.ticker}
    except Exception as e:
        logging.error(f"Error adding position: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/positions/bulk")
async def bulk_import_positions(user_id: str, request: PositionsBulkImport):
    try:
        portfolio_svc = PortfolioService()
        count = 0
        for p in request.positions:
            pos = Position(
                user_id=user_id,
                ticker=p.ticker.upper(),
                shares=p.shares,
                avg_cost=p.avg_cost,
                opened_at=datetime.utcnow(),
                status="open"
            )
            portfolio_svc.add_position(pos)
            count += 1
        return {"status": "success", "count": count}
    except Exception as e:
        logging.error(f"Error bulk importing positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/positions/upload")
async def upload_csv_positions(user_id: str, file: UploadFile = File(...), overwrite: bool = Form(False)):
    """Receives a raw CSV file and uses the LLM ExtractionService to intelligently parse any brokerage format"""
    if file.filename and not file.filename.endswith(".csv"):
         raise HTTPException(status_code=400, detail="Only CSV files are supported.")
         
    try:
        content_bytes = await file.read()
        csv_text = content_bytes.decode('utf-8', errors='replace')
        
        extractor = ExtractionService()
        parsed_positions = extractor.parse_csv_portfolio(csv_text)
        
        if not parsed_positions:
             # This could mean an unreadable file or simply no positions found
             return {"status": "success", "count": 0, "message": "No valid positions found or understood."}
             
        portfolio_svc = PortfolioService()
        
        # Process user intent to overwrite before adding new holdings
        if overwrite:
            portfolio_svc.clear_portfolio(user_id)
            
        count = 0
        for p in parsed_positions:
            # Safely cast LLM outputs
            try:
                pos = Position(
                    user_id=user_id,
                    ticker=str(p.get("ticker", "")).upper(),
                    shares=float(p.get("shares", 0)),
                    avg_cost=float(p.get("avg_cost", 0)),
                    opened_at=datetime.utcnow(),
                    status="open"
                )
                if pos.ticker and pos.shares > 0 and pos.avg_cost > 0:
                     portfolio_svc.add_position(pos)
                     count += 1
            except Exception as pe:
                 logging.warning(f"Failed to cast LLM extracted position: {p} -> {pe}")
                 continue # Skip invalid rows

        return {"status": "success", "count": count}
    except Exception as e:
        logging.error(f"Error processing AI CSV upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/positions/{ticker}")
async def update_position(user_id: str, ticker: str, request: PositionCreateUpdate):
    try:
        portfolio_svc = PortfolioService()
        pos = Position(
            user_id=user_id,
            ticker=ticker.upper(),
            shares=request.shares,
            avg_cost=request.avg_cost,
            opened_at=datetime.utcnow(),
            status="open"
        )
        portfolio_svc.add_position(pos)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error updating position {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/positions/{ticker}")
async def delete_position(user_id: str, ticker: str):
    try:
        portfolio_svc = PortfolioService()
        portfolio_svc.remove_position(user_id, ticker.upper())
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error deleting position {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
