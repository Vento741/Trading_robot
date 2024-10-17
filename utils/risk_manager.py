class RiskManager:
    def __init__(self, max_position_size: float, max_daily_loss: float, max_drawdown: float):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.daily_loss = 0
        self.peak_balance = 0
        self.current_balance = 0

    def calculate_position_size(self, price: float, account_balance: float) -> float:
        max_size = min(self.max_position_size, account_balance * 0.02)  # Не более 2% от баланса счета
        return max_size / price

    def update_balance(self, new_balance: float):
        self.current_balance = new_balance
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance

    def check_daily_loss(self, trade_result: float) -> bool:
        self.daily_loss += trade_result
        return self.daily_loss <= self.max_daily_loss

    def check_drawdown(self) -> bool:
        if self.peak_balance == 0:
            return True
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        return current_drawdown <= self.max_drawdown

    def can_open_position(self, trade_size: float) -> bool:
        return (trade_size <= self.max_position_size and
                self.check_daily_loss(0) and
                self.check_drawdown())

    def reset_daily_loss(self):
        self.daily_loss = 0