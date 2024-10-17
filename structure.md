trading_robot/
│
├── main.py                 # Точка входа в приложение
├── config.py               # Конфигурационный файл
│
├── exchange/
│   ├── __init__.py
│   ├── bybit_client.py     # Клиент для работы с Bybit API
│   └── data_fetcher.py     # Модуль для получения данных с биржи, classTradingRobot
│
├── strategies/
│   ├── __init__.py
│   ├── base_trading_robot.py    # Базовый класс для стратегий, classBaseTradingRobot
│   ├── strategy1.py        # Реализация стратегии 1
│   ├── strategy2.py        # Реализация стратегии 2
│   └── strategy3.py        # Реализация стратегии 3
│
├── models/
│   ├── __init__.py
│   ├── order.py            # Модель ордера
│   └── position.py         # Модель позиции
│
├── utils/
│   ├── __init__.py
│   ├── logger.py           # Модуль для логирования
│   └── risk_manager.py     # Модуль управления рисками
│
├── bot/
│   ├── __init__.py
│   └── telegram_bot.py     # Реализация Telegram бота
│
└── tests/                  # Директория для unit-тестов
    ├── __init__.py
    ├── test_strategies.py
    └── test_exchange.py
