from typing import Dict
from strategies.base_trading_robot import BaseTradingRobot
from models.order import Order
import ta
import pandas as pd

class ScalpingStrategy2(BaseTradingRobot):
    def __init__(self, api_key: str, api_secret: str, symbol: str, risk_manager):
        super().__init__(api_key, api_secret, symbol, risk_manager)
        self.bb_period = 20
        self.bb_std = 2
        self.stop_loss_pct = 0.003  # 0.3%
        self.take_profit_pct = 0.006  # 0.6%

    def analyze_market(self, market_data: Dict):
        close_prices = pd.Series(market_data['close'])
        self.bb = ta.volatility.BollingerBands(close=close_prices, window=self.bb_period, window_dev=self.bb_std)
        self.current_price = close_prices.iloc[-1]

    def execute_strategy(self):
        if self.current_price < self.bb.bollinger_lband().iloc[-1]:
            self.open_long_position()
        elif self.current_price > self.bb.bollinger_hband().iloc[-1]:
            self.open_short_position()

        self.manage_open_positions()

    def manage_open_positions(self):
        open_positions = self.get_open_positions()
        for position in open_positions:
            if (position.side == 'LONG' and self.current_price > self.bb.bollinger_mavg().iloc[-1]) or \
               (position.side == 'SHORT' and self.current_price < self.bb.bollinger_mavg().iloc[-1]):
                if self.close_position(position):
                    self.logger.info(f"Закрыта позиция: {position}")