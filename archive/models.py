"""
Data models for PolymarketLolBot.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Bet:
    """
    Represents a bet placed on Polymarket.
    """
    bet_id: Optional[int] = None
    order_id: Optional[str] = None
    token_id: str = ""
    market_id: Optional[str] = None
    market_question: str = ""
    outcome: str = ""
    side: str = "BUY"
    price: float = 0.0
    size: float = 0.0
    amount_spent: float = 0.0
    status: str = "pending"
    placed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    settled_price: Optional[float] = None
    pnl: Optional[float] = None
    roi: Optional[float] = None

    def to_dict(self):
        """
        Convert bet to dictionary, excluding None values.

        Returns:
            Dictionary with bet data
        """
        data = asdict(self)
        # Convert datetime objects to strings
        if self.placed_at:
            data['placed_at'] = self.placed_at.isoformat()
        if self.settled_at:
            data['settled_at'] = self.settled_at.isoformat()
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_db_row(cls, row):
        """
        Create Bet instance from database row.

        Args:
            row: SQLite Row object or dictionary

        Returns:
            Bet instance
        """
        # Convert row to dict if it's a Row object
        data = dict(row) if hasattr(row, 'keys') else row

        # Parse datetime strings if present
        if data.get('placed_at') and isinstance(data['placed_at'], str):
            data['placed_at'] = datetime.fromisoformat(data['placed_at'])
        if data.get('settled_at') and isinstance(data['settled_at'], str):
            data['settled_at'] = datetime.fromisoformat(data['settled_at'])

        return cls(**data)

    def calculate_pnl(self, settled_price: float) -> tuple[float, float]:
        """
        Calculate profit/loss and ROI for this bet.

        Args:
            settled_price: Final market price (1.0 for YES win, 0.0 for NO win)

        Returns:
            Tuple of (pnl, roi)
        """
        cost = self.price * self.size

        if self.side.upper() == 'BUY':
            if settled_price == 1.0:  # WIN
                payout = self.size
                pnl = payout - cost
            else:  # LOSE
                pnl = -cost
        else:  # SELL (short position)
            received = cost
            if settled_price == 0.0:  # WIN (outcome didn't happen)
                pnl = received
            else:  # LOSE
                payout = self.size
                pnl = received - payout

        roi = (pnl / cost * 100) if cost > 0 else 0.0

        return pnl, roi

    def __repr__(self):
        """String representation for debugging."""
        return (f"Bet(id={self.bet_id}, outcome={self.outcome}, "
                f"price=${self.price:.2f}, amount=${self.amount_spent:.2f}, "
                f"status={self.status})")
