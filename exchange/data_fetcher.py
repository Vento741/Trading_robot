import asyncio
import threading
import time
import logging
from typing import Dict, List
from exchange.bybit_client import BybitClient
from strategies.strategy1 import ScalpingStrategy1
from strategies.strategy2 import ScalpingStrategy2
from strategies.strategy3 import ScalpingStrategy3
from utils.risk_manager import RiskManager
from bot.telegram_bot import TelegramBot
from utils.strategy_visualizer import initialize_visualizer

class TradingRobot:
    def __init__(self, api_key: str, api_secret: str, symbols: List[str], telegram_token: str,
                 max_position_size: float, max_daily_loss: float, max_drawdown: float, active_strategy: str = "ScalpingStrategy1"):
        self.client = BybitClient(api_key, api_secret)
        self.risk_manager = RiskManager(max_position_size, max_daily_loss, max_drawdown)
        self.symbols = symbols
        self.strategies = {}
        self.is_running = False
        self.total_profit = 0
        self.logger = logging.getLogger(__name__)
        self.active_strategy = active_strategy

        strategy_class = globals()[active_strategy]
        for symbol in symbols:
            self.strategies[symbol] = strategy_class(api_key, api_secret, symbol, self.risk_manager)

        self.telegram_bot = TelegramBot(telegram_token, self)
        self.telegram_bot_thread = None
        self.bot_loop = None

        # Инициализация визуализатора
        initialize_visualizer(active_strategy)

    def start(self):
        self.is_running = True
        
        # Запускаем Telegram бота в отдельном потоке
        self.telegram_bot_thread = threading.Thread(target=self._run_telegram_bot)
        self.telegram_bot_thread.start()
        
        try:
            while self.is_running:
                for symbol in self.symbols:
                    try:
                        self.logger.info(f"Обработка символа: {symbol}")
                        market_data = self.client.get_market_data(symbol)
                        self.logger.info(f"Получены рыночные данные для {symbol}")
                        strategy = self.strategies[symbol]
                        self.logger.info(f"Выполнение стратегии {type(strategy).__name__} для {symbol}")
                        strategy.analyze_market(market_data)
                        strategy.execute_strategy()
                        
                        self.update_profit(symbol)
                    except Exception as e:
                        self.logger.error(f"Ошибка при обработке символа {symbol}: {str(e)}", exc_info=True)
                
                time.sleep(10)  # Пауза в 10 секунд между итерациями
        except Exception as e:
            self.logger.error(f"Ошибка в основном цикле: {str(e)}", exc_info=True)
        finally:
            self.stop()

    def change_strategy(self, new_strategy: str):
        if new_strategy not in ["ScalpingStrategy1", "ScalpingStrategy2", "ScalpingStrategy3"]:
            raise ValueError("Неподдерживаемая стратегия")
        
        self.active_strategy = new_strategy
        strategy_class = globals()[new_strategy]
        for symbol in self.symbols:
            self.strategies[symbol] = strategy_class(self.client.api_key, self.client.api_secret, symbol, self.risk_manager)
        
        self.logger.info(f"Стратегия изменена на {new_strategy}")


    def _run_telegram_bot(self):
        self.bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.bot_loop)
        self.bot_loop.run_until_complete(self.telegram_bot.run())

    def stop(self):
        self.logger.info("Остановка торгового робота...")
        self.is_running = False
        if self.bot_loop:
            self.bot_loop.call_soon_threadsafe(self._stop_telegram_bot)
        if self.telegram_bot_thread:
            self.telegram_bot_thread.join()
        self.logger.info("Торговый робот остановлен.")

    def _stop_telegram_bot(self):
        async def stop_bot():
            await self.telegram_bot.stop()
        self.bot_loop.create_task(stop_bot())
        self.bot_loop.stop()

    def update_profit(self, symbol: str):
        try:
            positions = self.client.get_open_positions(symbol)
            for position in positions:
                self.total_profit += position.unrealized_pnl
            self.risk_manager.update_balance(self.client.get_account_balance())
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прибыли для {symbol}: {str(e)}")

    def get_status(self) -> Dict:
        try:
            return {
                "is_running": self.is_running,
                "total_profit": self.total_profit,
                "open_positions": self.client.get_open_positions(self.symbols[0]),  # Получаем позиции только для первого символа
                "account_balance": self.client.get_account_balance()
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статуса: {str(e)}")
            return {"error": str(e)}

    def enable(self):
        self.is_running = True

    def disable(self):
        self.is_running = False

    def get_total_profit(self) -> float:
        return self.total_profit