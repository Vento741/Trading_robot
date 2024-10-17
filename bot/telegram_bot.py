import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

class TelegramBot:
    def __init__(self, token: str, trading_robot):
        self.application = Application.builder().token(token).build()
        self.trading_robot = trading_robot

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("enable", self.enable))
        self.application.add_handler(CommandHandler("disable", self.disable))
        self.application.add_handler(CommandHandler("profit", self.profit))

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Привет! Я бот для управления торговым роботом. '
                                        'Используйте команды /status, /enable, /disable, /profit для управления.')

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        status = self.trading_robot.get_status()
        await update.message.reply_text(f'Статус торгового робота: {status}')

    async def enable(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.trading_robot.enable()
        await update.message.reply_text('Торговый робот включен.')

    async def disable(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.trading_robot.disable()
        await update.message.reply_text('Торговый робот выключен.')

    async def profit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        profit = self.trading_robot.get_total_profit()
        await update.message.reply_text(f'Общая прибыль: {profit:.2f} USDT')

    async def send_notification(self, message: str) -> None:
        # В реальном приложении здесь нужно реализовать логику хранения и управления подписками пользователей
        await self.application.bot.send_message(chat_id=self.trading_robot.config.ADMIN_CHAT_ID, text=message)

    async def run(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop(self):
        await self.application.stop()
        await self.application.shutdown()