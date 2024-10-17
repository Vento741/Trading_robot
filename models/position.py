from dataclasses import dataclass
from typing import Optional

@dataclass
class Position:
    symbol: str
    side: str  # 'LONG' или 'SHORT'
    amount: float
    entry_price: float
    liquidation_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    leverage: Optional[float] = None

    def __str__(self):
        return (f"Position(symbol={self.symbol}, side={self.side}, amount={self.amount}, "
                f"entry_price={self.entry_price}, liquidation_price={self.liquidation_price}, "
                f"unrealized_pnl={self.unrealized_pnl}, leverage={self.leverage})")

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "entryPrice": self.entry_price,
            "liquidationPrice": self.liquidation_price,
            "unrealizedPnl": self.unrealized_pnl,
            "leverage": self.leverage
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol=data['symbol'],
            side=data['side'],
            amount=data['amount'],
            entry_price=data['entryPrice'],
            liquidation_price=data.get('liquidationPrice'),
            unrealized_pnl=data.get('unrealizedPnl'),
            leverage=data.get('leverage')
        )

    def update_unrealized_pnl(self, current_price: float):
        if self.side == 'LONG':
            self.unrealized_pnl = (current_price - self.entry_price) * self.amount
        elif self.side == 'SHORT':
            self.unrealized_pnl = (self.entry_price - current_price) * self.amount