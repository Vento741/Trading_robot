import logging
import sys
from exchange.data_fetcher import TradingRobot
import config

def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Создание и запуск торгового робота
    robot = TradingRobot(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        symbols=config.SYMBOLS,
        telegram_token=config.TELEGRAM_TOKEN,
        max_position_size=config.MAX_POSITION_SIZE,
        max_daily_loss=config.MAX_DAILY_LOSS,
        max_drawdown=config.MAX_DRAWDOWN,
        active_strategy=config.ACTIVE_STRATEGY
    )

    try:
        logger.info("Запуск торгового робота...")
        robot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания. Остановка торгового робота...")
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
    finally:
        robot.stop()
        logger.info("Торговый робот остановлен.")
        sys.exit(0)

if __name__ == "__main__":
    main()
