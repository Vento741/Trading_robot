import numpy as np
from typing import Dict
from strategies.base_trading_robot import BaseTradingRobot
import ta
import pandas as pd
from utils.strategy_visualizer import update_visualizer
from datetime import datetime
from models.position import Position
from models.order import Order

class ScalpingStrategy1(BaseTradingRobot):
    def __init__(self, api_key: str, api_secret: str, symbol: str, risk_manager):
        super().__init__(api_key, api_secret, symbol, risk_manager)
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.stop_loss_pct = 0.005  # 0.5%
        self.take_profit_pct = 0.01  # 1%
        self.trailing_stop_pct = 0.003  # 0.3%
        self.partial_close_pct = 0.5  # 50% частичное закрытие
        self.current_position = None
        self.max_positions = 4  # Максимальное количество открытых позиций
        self.position_size_pct = 0.1  # 10% от доступного баланса на одну позицию
        self.open_positions = []
        self.trend_period = 20  # Период для определения тренда
        self.trend_threshold = 0.01  # Порог для определения тренда (1%)

    def analyze_market(self, market_data: Dict):
        self.update_positions()  # Обновляем информацию о позициях перед анализом

        # Преобразуем списки в pandas Series
        high = pd.Series(market_data['high'])
        low = pd.Series(market_data['low'])
        close_prices = pd.Series(market_data['close'])
        volume = pd.Series(market_data['volume'])

        self.rsi = ta.momentum.RSIIndicator(close_prices, self.rsi_period).rsi()
        self.current_price = close_prices.iloc[-1]
        self.atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close_prices, window=14).average_true_range()
        
        conditions = {
            "RSI": self.rsi.iloc[-1],
            "Цена": self.current_price,
            "Объем": volume.iloc[-1],
            "Тренд": close_prices.pct_change(5).mean() * 100,  # 5-периодный тренд
            "ATR": self.atr.iloc[-1]
        }
        
        position_data = self._get_position_data()
        
        update_visualizer(self.symbol, conditions, position_data)

    def update_positions(self):
        # Получаем актуальную информацию о позициях с биржи
        exchange_positions = self.get_open_positions()
        
        # Обновляем наш список открытых позиций
        self.open_positions = []
        for pos in exchange_positions:
            if pos.symbol == self.symbol:
                self.open_positions.append(pos)
                self.current_position = pos  # Обновляем текущую позицию

    def execute_strategy(self):
        if len(self.open_positions) < self.max_positions:
            if self.rsi.iloc[-1] < self.rsi_oversold and self._check_trend('up'):
                self.open_long_position(self.current_price)
            elif self.rsi.iloc[-1] > self.rsi_overbought and self._check_trend('down'):
                self.open_short_position(self.current_price)

        self.manage_open_positions()

    def _get_position_data(self) -> Dict:
        """
        Формирует словарь с данными о текущей позиции.
        
        :return: словарь с данными о позиции
        """
        if not self.current_position:
            return {
                "Позиция": "Нет",
                "SL": "Нет",
                "TP": "Нет",
                "Цена входа": "Нет",
                "Текущая цена": self.current_price,
                "Цена добора": "Нет",
                "Частичное закрытие": "Нет"
            }
        
        average_down_price = self._calculate_average_down_price(self.current_position)
        partial_close_price = self.current_position.entry_price * (1 + self.partial_close_pct if self.current_position.side == 'LONG' else 1 - self.partial_close_pct)
        
        return {
            "Позиция": self.current_position.side,
            "SL": self.current_position.stop_loss,
            "TP": self.current_position.take_profit,
            "Цена входа": self.current_position.entry_price,
            "Текущая цена": self.current_price,
            "Цена добора": f"{average_down_price:.2f}",
            "Частичное закрытие": f"{self.partial_close_pct * 100}% at {partial_close_price:.2f}"
        }


    def open_long_position(self, price):
        available_balance = self.get_available_balance()
        position_size = available_balance * self.position_size_pct
        quantity = position_size / price
        
        stop_loss = price * (1 - self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct)
        
        order = self.place_order(
            symbol=self.symbol,
            side="BUY",
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if order:
            self.current_position = Position("LONG", price, stop_loss, take_profit, quantity)
            self.open_positions.append(self.current_position)
            self.logger.info(f"Открыта длинная позиция по цене {price}")

    def open_short_position(self, price):
        available_balance = self.get_available_balance()
        position_size = available_balance * self.position_size_pct
        quantity = position_size / price
        
        stop_loss = price * (1 + self.stop_loss_pct)
        take_profit = price * (1 - self.take_profit_pct)
        
        order = self.place_order(
            symbol=self.symbol,
            side="SELL",
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if order:
            self.current_position = Position("SHORT", price, stop_loss, take_profit, quantity)
            self.open_positions.append(self.current_position)
            self.logger.info(f"Открыта короткая позиция по цене {price}")

    def manage_open_positions(self):
        for position in self.open_positions:
            if position.side == 'LONG':
                if self.current_price >= position.entry_price * (1 + self.partial_close_pct):
                    self._partial_close(position)
                self._update_stop_loss_order(position)
            elif position.side == 'SHORT':
                if self.current_price <= position.entry_price * (1 - self.partial_close_pct):
                    self._partial_close(position)
                self._update_stop_loss_order(position)

    def _partial_close(self, position):
        close_quantity = position.quantity * self.partial_close_pct
        self._close_position(position, close_quantity)
        position.quantity -= close_quantity
        self.logger.info(f"Частично закрыта позиция: {position}")

    def _close_position(self, position, quantity=None):
        if quantity is None:
            quantity = position.quantity
        
        order = self.place_order(
            symbol=self.symbol,
            side="SELL" if position.side == "LONG" else "BUY",
            quantity=quantity,
            price=self.current_price
        )
        
        if order:
            self.logger.info(f"Закрыта позиция: {position}")
            if quantity == position.quantity:
                self.open_positions.remove(position)
            else:
                position.quantity -= quantity

    def _update_trailing_stop(self, position):
        if position.side == 'LONG':
            new_stop_loss = self.current_price * (1 - self.trailing_stop_pct)
            if new_stop_loss > position.stop_loss:
                position.stop_loss = new_stop_loss
                self._update_stop_loss_order(position)
        elif position.side == 'SHORT':
            new_stop_loss = self.current_price * (1 + self.trailing_stop_pct)
            if new_stop_loss < position.stop_loss:
                position.stop_loss = new_stop_loss
                self._update_stop_loss_order(position)

    def _update_stop_loss_order(self, position: Position):
        """
        Обновляет ордер стоп-лосс на бирже, реализуя механизм трейлинг-стопа.
        
        :param position: текущая открытая позиция
        """
        current_price = self.current_price
        new_stop_loss = None

        if position.side == 'LONG':
            # Для длинной позиции двигаем стоп-лосс вверх
            potential_stop_loss = current_price * (1 - self.trailing_stop_pct)
            if potential_stop_loss > position.stop_loss:
                new_stop_loss = potential_stop_loss
        elif position.side == 'SHORT':
            # Для короткой позиции двигаем стоп-лосс вниз
            potential_stop_loss = current_price * (1 + self.trailing_stop_pct)
            if potential_stop_loss < position.stop_loss:
                new_stop_loss = potential_stop_loss
        
        if new_stop_loss:
            try:
                # Создаем новый ордер стоп-лосс
                order = Order(
                    symbol=self.symbol,
                    side='SELL' if position.side == 'LONG' else 'BUY',
                    order_type='STOP',
                    quantity=position.quantity,
                    price=new_stop_loss,
                    stop_loss=new_stop_loss  # Устанавливаем стоп-лосс
                )
                
                # Отменяем предыдущий стоп-лосс ордер, если он есть
                if position.stop_loss_order_id:
                    self._cancel_order(self.symbol, position.stop_loss_order_id)
                
                # Размещаем новый стоп-лосс ордер
                if self.place_order(order):
                    position.stop_loss = new_stop_loss
                    position.stop_loss_order_id = order.order_id  # Предполагаем, что Order имеет атрибут order_id
                    self.logger.info(f"Обновлен трейлинг-стоп для позиции: {position}. Новый стоп-лосс: {new_stop_loss:.2f}")
                else:
                    self.logger.error(f"Не удалось обновить трейлинг-стоп для позиции: {position}")
            except Exception as e:
                self.logger.error(f"Ошибка при обновлении трейлинг-стопа: {str(e)}")

    def _cancel_order(self, symbol: str, order_id: str):
        """
        Отменяет ордер на бирже.
        
        :param symbol: символ торговой пары
        :param order_id: ID ордера для отмены
        """
        try:
            self.client.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Ордер {order_id} для {symbol} успешно отменен")
        except Exception as e:
            self.logger.error(f"Ошибка при отмене ордера {order_id} для {symbol}: {str(e)}")

    def _check_trend(self, direction: str) -> bool:
        """
        Проверяет текущий тренд рынка.
        
        :param direction: 'up' для восходящего тренда, 'down' для нисходящего
        :return: True, если тренд соответствует указанному направлению, иначе False
        """
        close_prices = self.fetch_market_data()['close']
        trend = (close_prices[-1] - close_prices[-self.trend_period]) / close_prices[-self.trend_period]
        
        if direction == 'up':
            return trend > self.trend_threshold
        elif direction == 'down':
            return trend < -self.trend_threshold
        else:
            raise ValueError("Направление тренда должно быть 'up' или 'down'")

    def _calculate_average_down_price(self, position: Position) -> float:
        """
        Рассчитывает цену для усреднения позиции.
        
        :param position: текущая открытая позиция
        :return: цена для усреднения позиции
        """
        current_price = self.current_price
        entry_price = position.entry_price
        
        if position.side == 'LONG':
            # Для длинной позиции усредняем вниз
            average_down_price = entry_price * (1 - self.atr.iloc[-1] / entry_price)
            return max(average_down_price, current_price * 0.98)  # Не более 2% ниже текущей цены
        elif position.side == 'SHORT':
            # Для короткой позиции усредняем вверх
            average_up_price = entry_price * (1 + self.atr.iloc[-1] / entry_price)
            return min(average_up_price, current_price * 1.02)  # Не более 2% выше текущей цены
        else:
            raise ValueError("Неизвестный тип позиции")
        
    def get_available_balance(self) -> float:
        """
        Получает доступный баланс для торговли.
        
        :return: доступный баланс в USDT
        """
        return self.client.get_available_balance()


class Position:
    def __init__(self, side, entry_price, stop_loss, take_profit, quantity):
        self.side = side
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.quantity = quantity
        self.stop_loss_order_id = None  # Добавляем новый атрибут

    def __str__(self):
        return f"Position({self.side}, entry={self.entry_price}, SL={self.stop_loss}, TP={self.take_profit}, quantity={self.quantity}, SL_order_id={self.stop_loss_order_id})"