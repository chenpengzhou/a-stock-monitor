#!/usr/bin/env python3
"""
Bull 策略回测引擎 (BaoStock 数据版)

使用真实 BaoStock 数据进行回测
"""

import sys
import os
import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from tqdm import tqdm

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
from data.baostock_data import BaoStockData, BullDataLoader


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000
    transaction_cost: float = 0.001
    slippage: float = 0.001
    start_date: str = '20200101'
    end_date: str = '20201231'
    rebalance_freq: str = 'monthly'
    adjust: str = '2'


class BullBacktestEngine:
    """Bull 策略回测引擎"""
    
    def __init__(self, config: BacktestConfig = None):
        """初始化"""
        self.config = config or BacktestConfig()
        self.data_loader = BullDataLoader()
        self.cash = self.config.initial_capital
        self.positions = {}  # {stock_code: quantity}
        self.portfolio_value = []
        
    def load_data(self, stock_codes: List[str]) -> Dict[str, pd.DataFrame]:
        """加载数据"""
        print(f"📥 加载 {len(stock_codes)} 只股票数据...")
        return self.data_loader.load_stock_data(
            stock_codes,
            self.config.start_date,
            self.config.end_date
        )
    
    def run(self, stock_data: Dict[str, pd.DataFrame]) -> Dict:
        """运行回测"""
        print(f"🚀 开始回测...")
        print(f"   初始资金: {self.config.initial_capital:,.0f}")
        print(f"   回测期间: {self.config.start_date} ~ {self.config.end_date}")
        
        # 获取交易日列表
        dates = sorted(set())
        for df in stock_data.values():
            if not df.empty and 'date' in df.columns:
                dates.update(df['date'].tolist())
        
        dates = sorted(list(dates))
        print(f"   交易日数: {len(dates)}")
        
        # 获取每月调仓日
        rebalance_dates = self._get_rebalance_dates(dates)
        print(f"   调仓次数: {len(rebalance_dates)}")
        
        # 运行回测
        for i, date in enumerate(tqdm(dates, desc="回测")):
            # 计算当日组合价值
            daily_value = self.cash
            for code, qty in self.positions.items():
                if code in stock_data:
                    df = stock_data[code]
                    row = df[df['date'] == date]
                    if not row.empty:
                        price = row['close'].iloc[0]
                        daily_value += qty * price
            
            self.portfolio_value.append({
                'date': date,
                'value': daily_value
            })
            
            # 调仓日操作
            if date in rebalance_dates:
                self._rebalance(stock_data, date)
        
        # 计算绩效指标
        returns = self._calculate_returns()
        
        return {
            'total_return': returns['total_return'],
            'annualized_return': returns['annualized_return'],
            'max_drawdown': returns['max_drawdown'],
            'sharpe_ratio': returns['sharpe_ratio'],
            'portfolio_value': self.portfolio_value,
            'trades': []  # 交易记录
        }
    
    def _get_rebalance_dates(self, dates: List[str]) -> List[str]:
        """获取调仓日"""
        if self.config.rebalance_freq == 'monthly':
            # 每月第一个交易日
            rebalance = []
            current_month = None
            for date in dates:
                month = date[:6]
                if month != current_month:
                    rebalance.append(date)
                    current_month = month
            return rebalance
        return [dates[0]]
    
    def _rebalance(self, stock_data: Dict[str, pd.DataFrame], date: str):
        """调仓"""
        # 计算各股票动量得分
        scores = {}
        for code, df in stock_data.items():
            if df.empty:
                continue
            
            # 过去3个月涨幅
            df_hist = df[df['date'] <= date].tail(60)
            if len(df_hist) < 30:
                continue
            
            start_price = df_hist['close'].iloc[0]
            end_price = df_hist['close'].iloc[-1]
            momentum = (end_price - start_price) / start_price
            scores[code] = momentum
        
        # 选择动量最强的10只
        if len(scores) > 10:
            top_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            top_stocks = list(scores.items())
        
        # 计算目标仓位
        position_per_stock = self.cash / len(top_stocks) if top_stocks else 0
        
        # 交易
        for code, score in top_stocks:
            if code in stock_data:
                df = stock_data[code]
                row = df[df['date'] == date]
                if not row.empty:
                    price = row['close'].iloc[0]
                    target_qty = int(position_per_stock / price)
                    
                    if code in self.positions:
                        # 调整仓位
                        current_qty = self.positions[code]
                        diff = target_qty - current_qty
                    else:
                        # 新建仓位
                        diff = target_qty
                    
                    if diff > 0:
                        cost = diff * price * (1 + self.config.transaction_cost)
                        if cost <= self.cash:
                            self.cash -= cost
                            self.positions[code] = self.positions.get(code, 0) + diff
                    elif diff < 0:
                        revenue = abs(diff) * price * (1 - self.config.transaction_cost)
                        self.cash += revenue
                        self.positions[code] = self.positions.get(code, 0) + diff
    
    def _calculate_returns(self) -> Dict:
        """计算收益指标"""
        if not self.portfolio_value:
            return {}
        
        values = [v['value'] for v in self.portfolio_value]
        returns = np.diff(values) / values[:-1]
        returns = returns[~np.isnan(returns)]
        returns = returns[~np.isinf(returns)]
        
        total_return = (values[-1] - values[0]) / values[0]
        annual_return = total_return / (len(values) / 252) if len(values) > 252 else total_return
        
        # 最大回撤
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
        
        # 夏普比率
        sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annual_return,
            'max_drawdown': -max_dd,
            'sharpe_ratio': sharpe
        }


def main():
    """主函数 - 测试回测"""
    print("\n" + "="*60)
    print("🚀 Bull 策略回测 (BaoStock 数据)")
    print("="*60 + "\n")
    
    # 配置
    config = BacktestConfig(
        initial_capital=1000000,
        start_date='20200101',
        end_date='20201231'
    )
    
    # 创建引擎
    engine = BullBacktestEngine(config)
    
    # 测试股票列表 (取上证50成分股部分)
    stock_codes = [
        'sh.600000', 'sh.600036', 'sh.600519', 'sh.601398', 'sh.601988',
        'sh.601857', 'sh.601288', 'sh.601328', 'sh.601166', 'sh.600036'
    ]
    
    # 加载数据
    data = engine.load_data(stock_codes)
    
    if not data:
        print("❌ 数据加载失败")
        return
    
    print(f"✅ 成功加载 {len(data)} 只股票数据")
    
    # 运行回测
    result = engine.run(data)
    
    # 输出结果
    print(f"\n📊 回测结果:")
    print(f"   总收益: {result['total_return']*100:.2f}%")
    print(f"   年化收益: {result['annualized_return']*100:.2f}%")
    print(f"   最大回撤: {result['max_drawdown']*100:.2f}%")
    print(f"   夏普比率: {result['sharpe_ratio']:.2f}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
