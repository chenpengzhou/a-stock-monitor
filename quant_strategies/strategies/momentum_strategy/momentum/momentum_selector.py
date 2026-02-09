#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量策略选股器
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/commodity-monitor/src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from factors import MomentumFactors


class MomentumStrategy:
    """动量策略选股器"""
    
    def __init__(self, config=None):
        """初始化
        
        Args:
            config: dict, 策略配置
                - stock_pool: 选股池
                - weights: dict, 因子权重
                - top_n: int, 选股数量
                - market_type: str, 'all'/'main'/'gem'
        """
        self.config = config or {
            'weights': None,  # 默认等权重
            'top_n': 10,
            'market_type': 'all',
        }
        
        self.factors = MomentumFactors()
    
    def select_stocks(self, stock_data, factors_data):
        """选股
        
        Args:
            stock_data: DataFrame, 股票数据（收盘价、成交量等）
            factors_data: DataFrame, 因子数据
        
        Returns:
            DataFrame: 选中的股票及得分
        """
        # 获取权重
        weights = self.config.get('weights')
        
        # 计算综合得分
        scores = self.factors.calculate_composite_score(factors_data, weights)
        
        # 排名选股
        scores = scores.sort_values(ascending=False)
        top_stocks = scores.head(self.config['top_n'])
        
        result = pd.DataFrame({
            'code': top_stocks.index,
            'score': top_stocks.values
        })
        
        return result
    
    def run(self, data_dict):
        """运行策略（每3个月调用一次）
        
        Args:
            data_dict: dict, {股票代码: DataFrame}
        
        Returns:
            DataFrame: 选股结果
        """
        all_scores = []
        
        for code, data in data_dict.items():
            if len(data) < 252:  # 需要至少1年数据
                continue
            
            try:
                # 计算因子
                factors = self.factors.calculate_all_factors(data)
                
                # 计算综合得分
                score = self.factors.calculate_composite_score(
                    factors, 
                    self.config.get('weights')
                ).iloc[-1]  # 取最新值
                
                all_scores.append({
                    'code': code,
                    'score': score
                })
            except Exception as e:
                continue
        
        if not all_scores:
            return pd.DataFrame()
        
        # 合并得分并排序
        result = pd.DataFrame(all_scores)
        result = result.sort_values('score', ascending=False)
        
        # 选取top_n
        result = result.head(self.config['top_n'])
        
        return result
    
    def get_holdings(self, rebalance_date, stock_list):
        """获取调仓日持仓
        
        Args:
            rebalance_date: datetime, 调仓日期
            stock_list: list, 股票代码列表
        
        Returns:
            list: 持仓股票
        """
        return stock_list[:self.config['top_n']]
    
    def calculate_position_size(self, capital, stock_list, risk_params=None):
        """计算各股票仓位
        
        Args:
            capital: float, 总资金
            stock_list: list, 股票列表
            risk_params: dict, 风险参数
        
        Returns:
            dict: {股票代码: 仓位比例}
        """
        n = len(stock_list)
        
        if n == 0:
            return {}
        
        # 等权重分配
        position = 1.0 / n
        
        return {stock: position for stock in stock_list}
    
    def calculate_stop_loss(self, entry_price, current_price, stop_loss_pct):
        """计算止损信号
        
        Args:
            entry_price: float, 买入价格
            current_price: float, 当前价格
            stop_loss_pct: float, 止损比例
        
        Returns:
            bool: 是否触发止损
        """
        return (current_price - entry_price) / entry_price < -stop_loss_pct
    
    def should_rebalance(self, last_rebalance, current_date, interval_months=3):
        """判断是否需要调仓
        
        Args:
            last_rebalance: datetime, 上次调仓日期
            current_date: datetime, 当前日期
            interval_months: int, 调仓间隔（月）
        
        Returns:
            bool: 是否需要调仓
        """
        months_diff = (current_date.year - last_rebalance.year) * 12 + \
                      (current_date.month - last_rebalance.month)
        
        return months_diff >= interval_months


if __name__ == '__main__':
    print("动量策略选股器测试")
    
    strategy = MomentumStrategy({
        'top_n': 10,
        'weights': None,
    })
    
    print(f"默认持仓数量: {strategy.config['top_n']}")
    print("策略初始化完成")
