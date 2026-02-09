#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量策略回测框架
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/commodity-monitor/src')

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from momentum_selector import MomentumStrategy


class MomentumBacktest:
    """动量策略回测"""
    
    def __init__(self, config=None):
        """初始化
        
        Args:
            config: dict, 回测配置
        """
        self.config = config or {
            'initial_capital': 100000,
            'rebalance_months': 3,
            'stop_loss': 0.15,
            'take_profit': None,
            'position_size': 0.8,
            'market_type': 'all',
        }
        
        self.strategy = MomentumStrategy({
            'top_n': 10,
            'weights': None,
            'market_type': self.config['market_type'],
        })
        
        # 回测结果
        self.results = None
        self.trades = []
        self.positions = {}
    
    def run_backtest(self, stock_data_dict, start_date, end_date):
        """运行回测
        
        Args:
            stock_data_dict: dict, {股票代码: DataFrame(包含close, volume等)}
            start_date: datetime, 回测开始日期
            end_date: datetime, 回测结束日期
        
        Returns:
            dict: 回测结果
        """
        capital = self.config['initial_capital']
        last_rebalance = start_date
        holdings = {}  # 当前持仓 {code: {'shares': xxx, 'cost': xxx}}
        
        # 记录每日资产
        daily_values = []
        
        current_date = start_date
        
        while current_date <= end_date:
            # 检查是否需要调仓
            if self.strategy.should_rebalance(last_rebalance, current_date, 
                                              self.config['rebalance_months']):
                # 选股
                selected = self.strategy.run(stock_data_dict)
                
                if not selected.empty:
                    # 计算目标仓位
                    top_stocks = selected['code'].tolist()
                    n_stocks = len(top_stocks)
                    
                    if n_stocks > 0:
                        # 平仓
                        for code, pos in list(holdings.items()):
                            if code not in top_stocks:
                                # 按收盘价平仓
                                last_close = stock_data_dict[code]['close'].iloc[-1]
                                capital += pos['shares'] * last_close
                                self.trades.append({
                                    'date': current_date,
                                    'action': 'sell',
                                    'code': code,
                                    'shares': pos['shares'],
                                    'price': last_close
                                })
                                del holdings[code]
                        
                        # 买入新股票
                        stock_capital = capital * self.config['position_size']
                        per_stock = stock_capital / n_stocks
                        
                        for code in top_stocks:
                            if code not in holdings:
                                last_close = stock_data_dict[code]['close'].iloc[-1]
                                shares = int(per_stock / last_close)
                                
                                if shares > 0:
                                    cost = shares * last_close
                                    capital -= cost
                                    
                                    holdings[code] = {
                                        'shares': shares,
                                        'cost': last_close
                                    }
                                    
                                    self.trades.append({
                                        'date': current_date,
                                        'action': 'buy',
                                        'code': code,
                                        'shares': shares,
                                        'price': last_close
                                    })
                    
                    last_rebalance = current_date
            
            # 计算当日资产
            total_value = capital
            for code, pos in holdings.items():
                if code in stock_data_dict:
                    last_close = stock_data_dict[code]['close'].iloc[-1]
                    total_value += pos['shares'] * last_close
            
            daily_values.append({
                'date': current_date,
                'value': total_value,
                'capital': capital
            })
            
            # 前进1天
            current_date += timedelta(days=1)
        
        # 计算收益
        initial_value = self.config['initial_capital']
        final_value = daily_values[-1]['value'] if daily_values else initial_value
        total_return = (final_value - initial_value) / initial_value * 100
        
        # 计算年化收益
        days = (end_date - start_date).days
        annual_return = ((final_value / initial_value) ** (365.0 / days) - 1) * 100 if days > 0 else 0
        
        # 计算最大回撤
        df = pd.DataFrame(daily_values)
        df['peak'] = df['value'].cummax()
        df['drawdown'] = (df['value'] - df['peak']) / df['peak'] * 100
        max_drawdown = df['drawdown'].min()
        
        self.results = {
            'initial_capital': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades),
            'daily_values': daily_values,
        }
        
        return self.results
    
    def save_results(self, output_dir):
        """保存结果
        
        Args:
            output_dir: str, 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON结果
        result_json = {
            'config': self.config,
            'results': {
                'initial_capital': self.results['initial_capital'],
                'final_value': self.results['final_value'],
                'total_return': round(self.results['total_return'], 2),
                'annual_return': round(self.results['annual_return'], 2),
                'max_drawdown': round(self.results['max_drawdown'], 2),
                'total_trades': self.results['total_trades'],
            }
        }
        
        with open(output_path / 'backtest_result.json', 'w') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
        
        # 保存交易记录
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            trades_df.to_csv(output_path / 'trades.csv', index=False)
        
        # 保存每日资产
        values_df = pd.DataFrame(self.results['daily_values'])
        values_df.to_csv(output_path / 'daily_values.csv', index=False)
        
        print(f"结果已保存到: {output_path}")


def run_simple_backtest():
    """简化回测测试"""
    
    print("="*60)
    print("动量策略回测（简化测试）")
    print("="*60)
    
    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    
    stock_data = {}
    for i in range(50):  # 50只股票
        code = f'600{100+i}'
        
        # 创建趋势上涨的股票数据
        trend = np.random.randn() * 0.001 + 0.0005  # 轻微上涨趋势
        close = np.cumsum(np.random.randn(len(dates)) * 2 + trend) + 100
        
        stock_data[code] = pd.DataFrame({
            'close': close,
            'volume': np.abs(np.random.randn(len(dates)) * 1000000 + 5000000)
        }, index=dates)
    
    # 运行回测
    backtest = MomentumBacktest({
        'initial_capital': 100000,
        'rebalance_months': 3,
        'stop_loss': 0.15,
        'position_size': 0.8,
        'market_type': 'all',
    })
    
    results = backtest.run_backtest(
        stock_data_dict=stock_data,
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    print(f"\n回测结果:")
    print(f"初始资金: {results['initial_capital']:,.0f}")
    print(f"最终价值: {results['final_value']:,.0f}")
    print(f"总收益: {results['total_return']:.2f}%")
    print(f"年化收益: {results['annual_return']:.2f}%")
    print(f"最大回撤: {results['max_drawdown']:.2f}%")
    print(f"交易次数: {results['total_trades']}")
    
    return backtest


if __name__ == '__main__':
    run_simple_backtest()
