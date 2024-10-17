import logging
from typing import Dict, List
from exchange.bybit_client import BybitClient
from models.order import Order
from models.position import Position
from utils.risk_manager import RiskManager

class BaseTradingRobot:
    def __init__(self, api_key: str, api_secret: str, symbol: str, risk_manager: RiskManager):
        self.client = BybitClient(api_key, api_secret)
        self.symbol = symbol
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(__name__)

    def analyze_market(self, market_data: Dict):
        raise NotImplementedError("Метод должен быть реализован в подклассе")

    def execute_strategy(self):
        raise NotImplementedError("Метод должен быть реализован в подклассе")

    def place_order(self, order: Order) -> bool:
        return self.client.place_order(order)

    def get_open_positions(self) -> List[Position]:
        return self.client.get_open_positions(self.symbol)

    def close_position(self, position: Position) -> bool:
        return self.client.close_position(position)

    def fetch_market_data(self) -> Dict:
        return self.client.get_market_data(self.symbol)

    def get_available_balance(self) -> float:
        return self.client.get_available_balance()

    def _check_trend(self, direction: str) -> bool:
        # Реализация проверки тренда
        return self.client.check_trend(direction)

    def _calculate_average_down_price(self, position: Position) -> float:
        # Реализация расчета цены усреднения
        return self.client.get_average_down_price(position)