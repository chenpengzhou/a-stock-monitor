#!/usr/bin/env python3
"""
LowVol 仓位管理模块
"""

from config import LowVolConfig


class LowVolPositionManager:
    """低波策略仓位管理器"""
    
    def __init__(self, config: Dict = None):
        """初始化"""
        self.config = LowVolConfig(config)
    
    def calculate_position(self, market_type: str, total_capital: float) -> float:
        """
        计算仓位金额
        
        Args:
            market_type: 市场类型
            total_capital: 总资金
        
        Returns:
            仓位金额
        """
        position_ratio = self.config.get_position(market_type)
        return total_capital * position_ratio
    
    def get_stop_loss(self, entry_price: float) -> float:
        """
        计算止损价
        
        Args:
            entry_price: 入场价格
        
        Returns:
            止损价
        """
        stop_loss = self.config.get('stop_loss', 0.10)
        return entry_price * (1 - stop_loss)
    
    def get_take_profit(self, entry_price: float) -> float:
        """
        计算止盈价
        
        Args:
            entry_price: 入场价格
        
        Returns:
            止盈价
        """
        take_profit = self.config.get('take_profit', 0.30)
        return entry_price * (1 + take_profit)


if __name__ == "__main__":
    print("LowVol Position Manager loaded")
    pm = LowVolPositionManager()
    print(f"Position for 100000 capital (bear): {pm.calculate_position('bear', 100000)}")
