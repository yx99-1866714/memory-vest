from typing import List, Optional
from app.models.position import Position, CashBalance
from app.infra.db import get_db_connection

class PortfolioService:
    def get_positions(self, user_id: str) -> List[Position]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM positions WHERE user_id = ? AND status = 'open'", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        return [Position(**dict(row)) for row in rows]

    def add_position(self, position: Position):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO positions (user_id, ticker, shares, avg_cost, opened_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (position.user_id, position.ticker, position.shares, position.avg_cost, position.opened_at.isoformat(), position.status)
        )
        conn.commit()
        conn.close()
    
    def get_cash_balance(self, user_id: str) -> Optional[CashBalance]:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM cash_balances WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return CashBalance(**dict(row))
        return None

    def upsert_cash_balance(self, balance: CashBalance):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO cash_balances (user_id, available_cash, currency, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                available_cash=excluded.available_cash,
                currency=excluded.currency,
                updated_at=excluded.updated_at
            """,
            (balance.user_id, balance.available_cash, balance.currency, balance.updated_at.isoformat())
        )
        conn.commit()
        conn.close()
