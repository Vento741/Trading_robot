from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    symbol: str
    side: str  # 'BUY' или 'SELL'
    order_type: str  # 'MARKET' или 'LIMIT'
    quantity: float
    price: Optional[float] = None  # Цена для лимитного ордера
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_id: Optional[str] = None  # ID ордера, присваиваемый биржей

    def __str__(self):
        return (f"Order(symbol={self.symbol}, side={self.side}, type={self.order_type}, "
                f"quantity={self.quantity}, price={self.price}, "
                f"stop_loss={self.stop_loss}, take_profit={self.take_profit})")

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "stopLoss": self.stop_loss,
            "takeProfit": self.take_profit,
            "orderId": self.order_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol=data['symbol'],
            side=data['side'],
            order_type=data['type'],
            quantity=data['quantity'],
            price=data.get('price'),
            stop_loss=data.get('stopLoss'),
            take_profit=data.get('takeProfit'),
            order_id=data.get('orderId')
        )