import typer
from app.infra.db import init_db
from app.cli import commands_report
from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService
from app.services.profile_service import ProfileService
from app.services.portfolio_service import PortfolioService
from app.models.profile import UserProfile
from app.models.position import Position, CashBalance
import uuid
from datetime import datetime
from rich.console import Console
import logging
from rich.logging import RichHandler

app = typer.Typer()
app.add_typer(commands_report.app, name="report", help="Report generation and delivery commands")

console = Console()

@app.callback()
def main_callback(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")):
    """MemoryVest - Beginner-friendly investing companion powered by EverMemOS"""
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )

@app.command()
def init():
    """Initialize the SQLite database schema."""
    init_db()
    typer.echo("MemoryVest database initialized. You can now start chatting.")

@app.command()
def chat(user_id: str = typer.Option("user_001", help="User ID session")):
    """Start an interactive chat loop."""
    console.print(f"[bold green]Starting MemoryVest chat for {user_id}... (type 'exit' to quit)[/bold green]")
    
    extractor = ExtractionService()
    memory_svc = MemoryService()
    profile_svc = ProfileService()
    portfolio_svc = PortfolioService()
    
    while True:
        user_input = typer.prompt(">")
        if user_input.lower() in ("exit", "quit"):
            break
            
        # Parse Intent using LLM
        current_profile = profile_svc.get_profile(user_id)
        current_positions = portfolio_svc.get_positions(user_id)
        current_cash_bal = portfolio_svc.get_cash_balance(user_id)
        cash_amt = current_cash_bal.available_cash if current_cash_bal else 0.0

        with console.status("[cyan]Thinking..."):
            logging.debug(f"Sending chat input to extraction service: {user_input}")
            extracted = extractor.parse_user_input(
                user_input=user_input, 
                current_profile=current_profile, 
                current_positions=current_positions, 
                current_cash=cash_amt
            )
            logging.debug(f"Extracted payload: {extracted}")
        
        # Apply structured updates
        profile_updates = extracted.get("profile_updates", {})
        if profile_updates and any(v is not None for v in profile_updates.values()):
            if current_profile:
                for k, v in profile_updates.items():
                    if v is not None:
                        if hasattr(current_profile, k):
                            setattr(current_profile, k, v)
                profile_svc.upsert_profile(current_profile)
            else:
                new_profile = UserProfile(
                    user_id=user_id,
                    email=profile_updates.get("email") or "demo@example.com", # Default if not specified
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
            console.print("[dim]Profile updated locally.[/dim]")

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
                console.print(f"[dim]Position added: {pos.ticker}[/dim]")
            except Exception as e:
                console.print(f"[red]Error parsing position: {e}[/red]")
        
        if extracted.get("cash_update") is not None:
            bal = CashBalance(
                user_id=user_id,
                available_cash=float(extracted["cash_update"]),
                updated_at=datetime.utcnow()
            )
            portfolio_svc.upsert_cash_balance(bal)
            console.print(f"[dim]Cash updated to ${bal.available_cash}[/dim]")
        
        # Save exact context to EverMemOS
        memory_note = extracted.get("memory_note")
        if memory_note:
            try:
                memory_svc.store_user_message(user_id=user_id, content=user_input)
                console.print("[dim]Memory stored in EverMemOS.[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to connect to EverMemOS: {e}[/red]")
            
        console.print(f"[bold blue]MemoryVest:[/bold blue] Understood. I've updated your preferences and portfolio where needed. My takeaway: {memory_note or 'Got it.'}")
        logging.debug("Chat iteration complete.")

if __name__ == "__main__":
    app()

