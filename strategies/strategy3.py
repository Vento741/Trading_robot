from typing import Dict
from strategies.base_trading_robot import BaseTradingRobot
from models.order import Order
import ta
import pandas as pd

class ScalpingStrategy3(BaseTradingRobot):
    def __init__(self, api_key: str, api_secret: str, symbol: str, risk_manager):
        super().__init__(api_key, api_secret, symbol, risk_manager)
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_period = 50
        self.stop_loss_pct = 0.004  # 0.4%
        self.take_profit_pct = 0.008  # 0.8%

    def analyze_market(self, market_data: Dict):
        close_prices = pd.Series(market_data['close'])
        self.macd = ta.trend.MACD(close_prices, self.macd_fast, self.macd_slow, self.macd_signal)
        self.ema = ta.trend.EMAIndicator(close_prices, self.ema_period)
        self.current_price = close_prices.iloc[-1]

    def execute_strategy(self):
        if self.macd.macd_diff().iloc[-1] > 0 and self.current_price > self.ema.ema_indicator().iloc[-1]:
            self.open_long_position()
        elif self.macd.macd_diff().iloc[-1] < 0 and self.current_price < self.ema.ema_indicator().iloc[-1]:
            self.open_short_position()

        self.manage_open_positions()

    def manage_open_positions(self):
        open_positions = self.get_open_positions()
        for position in open_positions:
            if (position.side == 'LONG' and self.macd.macd_diff().iloc[-1] < 0) or \
               (position.side == 'SHORT' and self.macd.macd_diff().iloc[-1] > 0):
                if self.close_position(position):
                    self.logger.info(f"Закрыта позиция: {position}")