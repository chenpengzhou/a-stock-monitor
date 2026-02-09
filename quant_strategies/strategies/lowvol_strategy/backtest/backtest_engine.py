"""
回测引擎模块
============

本模块提供低波动率策略的回测功能。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.lowvol_config import LowVolConfig
from ..selection import LowVolStockSelector
from ..position import PositionManager


class LowVolBacktest:
    """
    低波动率策略回测引擎
    """
    
    def __init__(
        self,
        config: LowVolConfig = None,
        selector: LowVolStockSelector = None,
        position_manager: PositionManager = None
    ):
        self.config = config or LowVolConfig()
        self.selector = selector or LowVolStockSelector(self.config)
        self.position_manager = PositionManager(self.config)
        
        self.data = None
        self.cash = self.config.INITIAL_CAPITAL
        self.positions = {}
        self.portfolio_value = self.config.INITIAL_CAPITAL
        
        self.trades = []
        self.portfolio_history = []
        self.daily_returns = []
        
        self.transaction_cost = self.config.TRANSACTION_COST
        self.slippage = self.config.SLIPPAGE
        
        self.rebalance_dates = []
        self._has_run = False
    
    def load_data(self, data: pd.DataFrame):
        """加载回测数据"""
        self.data = data.copy()
        
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
            self.data = self.data.sort_values(['code', 'date'])
    
    def get_rebalance_dates(
        self,
        data: pd.DataFrame = None,
        frequency: str = 'monthly'
    ) -> List[datetime]:
        """获取调仓日期列表"""
        if data is None:
            data = self.data
        
        if data is None or len(data) == 0:
            return []
        
        dates = data['date'].unique()
        dates = sorted(dates)
        
        if frequency == 'monthly':
            rebalance_dates = []
            current_month = None
            for date in dates:
                month = date.strftime('%Y-%m')
                if month != current_month:
                    rebalance_dates.append(date)
                    current_month = month
            return rebalance_dates
        else:
            return dates
    
    def select_stocks(self, date: datetime) -> List[str]:
        """在指定日期选股"""
        date_data = self.data[self.data['date'] == date].copy()
        
        if len(date_data) == 0:
            return []
        
        selected, details = self.selector.select(date_data, return_details=True)
        selected_stocks = selected[selected].index.tolist()
        
        return selected_stocks
    
    def execute_rebalance(
        self,
        date: datetime,
        selected_stocks: List[str]
    ) -> Dict:
        """执行调仓"""
        date_data = self.data[self.data['date'] == date].copy()
        date_data = date_data.set_index('code')
        
        target_weights = self.position_manager.calculate_equal_weight(selected_stocks)
        
        stock_industry = date_data['industry'].to_dict()
        target_weights = self.position_manager.apply_risk_controls(
            target_weights,
            stock_industry
        )
        
        current_value = self.cash
        for stock, shares in self.positions.items():
            if stock in date_data.index:
                price = date_data.loc[stock, 'close']
                current_value += shares * price
        
        target_value = current_value
        
        trades = {}
        sell_trades = []
        buy_trades = []
        
        # 卖出
        for stock, shares in self.positions.items():
            if stock not in target_weights or shares == 0:
                if stock in date_data.index:
                    price = date_data.loc[stock, 'close']
                    sell_price = price * (1 - self.slippage)
                    sell_value = shares * sell_price * (1 - self.transaction_cost)
                    
                    self.cash += sell_value
                    self.positions[stock] = 0
                    
                    sell_trades.append({
                        'date': date,
                        'stock': stock,
                        'action': 'SELL',
                        'shares': shares,
                        'price': price,
                        'value': sell_value
                    })
        
        # 买入
        for stock, weight in target_weights.items():
            if stock in date_data.index:
                target_shares_value = target_value * weight
                price = date_data.loc[stock, 'close']
                buy_price = price * (1 + self.slippage)
                
                shares_to_buy = int(target_shares_value / buy_price)
                cost = shares_to_buy * buy_price * (1 + self.transaction_cost)
                
                if self.cash >= cost:
                    shares = shares_to_buy
                else:
                    shares = int(self.cash / buy_price)
                    cost = shares * buy_price * (1 + self.transaction_cost)
                
                if shares > 0:
                    self.cash -= cost
                    self.positions[stock] = shares
                    
                    buy_trades.append({
                        'date': date,
                        'stock': stock,
                        'action': 'BUY',
                        'shares': shares,
                        'price': price,
                        'value': cost
                    })
        
        self.trades.extend(sell_trades)
        self.trades.extend(buy_trades)
        
        portfolio_value = self.cash
        for stock, shares in self.positions.items():
            if shares > 0 and stock in date_data.index:
                price = date_data.loc[stock, 'close']
                portfolio_value += shares * price
        
        self.portfolio_value = portfolio_value
        
        return {
            'date': date,
            'sell_trades': sell_trades,
            'buy_trades': buy_trades,
            'portfolio_value': portfolio_value,
            'num_holdings': len([s for s in self.positions.values() if s > 0])
        }
    
    def run(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        frequency: str = 'monthly'
    ) -> Dict:
        """运行回测"""
        if self.data is None:
            raise ValueError("请先加载数据：调用 load_data()")
        
        dates = self.data['date'].unique()
        dates = sorted(dates)
        
        if start_date:
            dates = [d for d in dates if d >= start_date]
        if end_date:
            dates = [d for d in dates if d <= end_date]
        
        if len(dates) == 0:
            raise ValueError("没有有效的回测日期")
        
        self.rebalance_dates = self.get_rebalance_dates(
            self.data[self.data['date'].isin(dates)],
            frequency
        )
        
        self.cash = self.config.INITIAL_CAPITAL
        self.positions = {}
        self.portfolio_value = self.config.INITIAL_CAPITAL
        self.trades = []
        self.portfolio_history = []
        self.daily_returns = []
        
        first_date = dates[0]
        
        if len(self.rebalance_dates) > 0:
            first_rebalance = self.rebalance_dates[0]
            selected = self.select_stocks(first_rebalance)
            if len(selected) > 0:
                self.execute_rebalance(first_rebalance, selected)
        
        self.portfolio_history.append({
            'date': first_date,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'positions_value': self.portfolio_value - self.cash
        })
        
        for i, date in enumerate(dates[1:], 1):
            if date in self.rebalance_dates:
                selected = self.select_stocks(date)
                self.execute_rebalance(date, selected)
            
            date_data = self.data[self.data['date'] == date].copy()
            date_data = date_data.set_index('code')
            
            portfolio_value = self.cash
            for stock, shares in self.positions.items():
                if shares > 0 and stock in date_data.index:
                    price = date_data.loc[stock, 'close']
                    portfolio_value += shares * price
            
            prev_value = self.portfolio_history[-1]['portfolio_value']
            daily_return = (portfolio_value - prev_value) / prev_value if prev_value > 0 else 0
            
            self.portfolio_value = portfolio_value
            self.daily_returns.append(daily_return)
            
            self.portfolio_history.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions_value': portfolio_value - self.cash,
                'daily_return': daily_return
            })
        
        self._has_run = True
        
        return self.get_results()
    
    def get_results(self) -> Dict:
        """获取回测结果"""
        if not self._has_run:
            return {}
        
        from .performance import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer()
        perf = analyzer.analyze(self.portfolio_history, self.trades)
        
        return perf
    
    def print_results(self):
        """打印回测结果"""
        if not self._has_run:
            print("请先运行回测：调用 run()")
            return
        
        results = self.get_results()
        
        print("\n" + "=" * 60)
        print("低波动率策略回测结果")
        print("=" * 60)
        
        print(f"\n【基本信息】")
        print(f"  回测期间: {results['回测期间']}")
        print(f"  交易日数: {results['交易日数']}")
        print(f"  调仓次数: {results['调仓次数']}")
        
        print(f"\n【收益表现】")
        print(f"  总收益率: {results['总收益率']:.2f}%")
        print(f"  年化收益率: {results['年化收益率']:.2f}%")
        print(f"  月均收益率: {results['月均收益率']:.2f}%")
        
        print(f"\n【风险指标】")
        print(f"  年化波动率: {results['年化波动率']:.2f}%")
        print(f"  最大回撤: {results['最大回撤']:.2f}%")
        print(f"  夏普比率: {results['夏普比率']:.2f}")
        
        print(f"\n【交易统计】")
        print(f"  总交易次数: {results['总交易次数']}")
        print(f"  平均换手率: {results['平均换手率']:.2f}%")
        
        print("=" * 60)
