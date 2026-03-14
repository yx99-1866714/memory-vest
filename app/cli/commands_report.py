import typer
from rich.console import Console
from app.services.report_service import ReportService
from app.services.profile_service import ProfileService
from app.services.portfolio_service import PortfolioService
from app.services.memory_service import MemoryService
from app.services.market_data_service import MarketDataService
from app.services.news_service import NewsService
from app.services.delivery_service import DeliveryService
import json

app = typer.Typer()
console = Console()

@app.command("preview")
def preview_report(user_id: str = typer.Option(..., help="User ID to generate report for")):
    """Preview the daily personalized report for a user."""
    with console.status("[bold green]Generating Report Preview...") as status:
        profile = ProfileService().get_profile(user_id)
        if not profile:
            typer.echo("User profile not found. Please initialize or chat first.")
            raise typer.Exit()
            
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
        report = report_service.generate_report(
            user_id=user_id,
            profile=profile.model_dump(mode='json'),
            positions=[p.model_dump(mode='json') for p in positions],
            cash=cash_amt,
            memory_context=memory_context,
            market_data=market_data,
            news_data=news_data
        )
        
        # Persist the full generated report content into SQLite History
        history_record = report_service.create_report_history_record(user_id, report)
        report_service.save_report_history(history_record)

    console.print(f"\n[bold blue]=== Report Preview for {user_id} ===[/bold blue]\n")
    console.print(report)

@app.command("send")
def send_report(user_id: str = typer.Option(..., help="User ID to send report to")):
    """Email the daily personalized report for a user."""
    profile = ProfileService().get_profile(user_id)
    if not profile or not profile.email:
        typer.echo("User profile or email not found.")
        raise typer.Exit()
        
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
    report = report_service.generate_report(
        user_id=user_id,
        profile=profile.model_dump(mode='json'),
        positions=[p.model_dump(mode='json') for p in positions],
        cash=cash_amt,
        memory_context=memory_context,
        market_data=market_data,
        news_data=news_data
    )
    
    # Persist the history to DB before sending via email
    history_record = report_service.create_report_history_record(user_id, report)
    report_service.save_report_history(history_record)
    
    DeliveryService().send_report(profile.email, f"MemoryVest Daily Report for {user_id}", report)
    typer.echo(f"Report sent to {profile.email}")
