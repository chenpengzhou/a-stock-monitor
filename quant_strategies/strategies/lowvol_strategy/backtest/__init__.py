#!/usr/bin/env python3
"""
LowVol 策略回测引擎

低波动防守策略回测
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from factors import LowVolFactor


class LowVolBacktest:
    """低波策略回测"""
    
    def __init__(self, config: Dict = None):
        """初始化
        
        Args:
            config: 回测配置
        """
        self.config = config or {
            'initial_capital': 100000,
            'rebalance_months': 3,
            'stop_loss': 0.10,
            'take_profit': 0.30,
            'position_size': 0.4,  # 熊市40%仓位
            'market_type': 'bear',  # 默认熊市
        }
        
        self.capital = self.config['initial_capital']
        self.factor = LowVolFactor()
        
        self.results = []
    
    def run(self, data: pd.DataFrame, market_returns: pd.Series = None) -> Dict:
        """
        运行回测
        
        Args:
            data: 股票数据 DataFrame
            market_returns: 市场收益序列
        
        Returns:
            回测结果
        """
        # 选股
        selected = self.factor.select_stocks(
            data, 
            market_returns,
            top_n=30,
            market_type=self.config['market_type']
        )
        
        # 计算收益
        returns = []
        for stock in selected:
            if stock in data.columns:
                stock_return = data[stock].pct_change().iloc[-1]
                returns.append(stock_return)
        
        if returns:
            avg_return = np.mean(returns)
        else:
            avg_return = 0
        
        # 更新资金
        position_value = self.capital * self.config['position_size']
        profit = position_value * avg_return
        self.capital += profit
        
        result = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'selected_count': len(selected),
            'avg_return': avg_return,
            'capital': self.capital,
            'total_return': (self.capital - self.config['initial_capital']) / self.config['initial_capital']
        }
        
        self.results.append(result)
        
        return result
    
    def get_summary(self) -> Dict:
        """获取回测汇总"""
        if not self.results:
            return {}
        
        returns = [r['total_return'] for r in self.results]
        
        return {
            'total_return': np.mean(returns),
            'annual_return': np.mean(returns) * 4,  # 季度回测，年化
            'max_drawdown': min(returns),
            'sharpe_ratio': np.mean(returns) / (np.std(returns) + 1e-8) if returns else 0,
        }


if __name__ == "__main__":
    print("LowVol Backtest Module loaded")
    bt = LowVolBacktest()
    print(f"Config: {bt.config}")
