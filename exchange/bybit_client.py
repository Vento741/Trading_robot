import ccxt
import pandas as pd
from typing import Dict, List
from models.order import Order
from models.position import Position

class BybitClient:
    def __init__(self, api_key: str, api_secret: str):
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })

    def get_market_data(self, symbol: str) -> Dict:
        ohlcv = self.exchange.fetch_ohlcv(symbol, '1m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return {
            'open': df['open'].tolist(),
            'high': df['high'].tolist(),
            'low': df['low'].tolist(),
            'close': df['close'].tolist(),
            'volume': df['volume'].tolist()
        }

    def place_order(self, order: Order) -> bool:
        try:
            result = self.exchange.create_order(
                symbol=order.symbol,
                type=order.order_type,
                side=order.side,
                amount=order.quantity,
                price=order.price,
                params={
                    'stopLoss': order.stop_loss,
                    'takeProfit': order.take_profit
                }
            )
            order.order_id = result['id']  # Сохраняем ID ордера
            return True
        except Exception as e:
            print(f"Ошибка при размещении ордера: {str(e)}")
            return False
        
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        try:
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Ошибка при отмене ордера: {str(e)}")
            return False

    def get_open_positions(self, symbol: str) -> List[Position]:
        try:
            positions = self.exchange.fetch_positions([symbol], {'category': 'linear'})
            return [Position(
                symbol=pos['symbol'],
                side='LONG' if pos['side'] == 'buy' else 'SHORT',
                amount=pos['contracts'],
                entry_price=pos['entryPrice'],
                liquidation_price=pos['liquidationPrice'],
                unrealized_pnl=pos['unrealizedPnl'],
                leverage=pos['leverage']
            ) for pos in positions if pos['contracts'] > 0]
        except Exception as e:
            print(f"Ошибка при получении открытых позиций: {str(e)}")
            return []

    def close_position(self, position: Position) -> bool:
        try:
            self.exchange.create_market_order(
                symbol=position.symbol,
                side='sell' if position.side == 'LONG' else 'buy',
                amount=position.amount,
                params={'reduce_only': True}
            )
            return True
        except Exception as e:
            print(f"Ошибка при закрытии позиции: {str(e)}")
            return False

    def get_account_balance(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            return balance['total']['USDT']
        except Exception as e:
            print(f"Ошибка при получении баланса аккаунта: {str(e)}")
            return 0.0