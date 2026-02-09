"""
绩效分析模块
============

本模块提供策略绩效分析功能。
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union


class PerformanceAnalyzer:
    """
    策略绩效分析器
    """
    
    TRADING_DAYS_PER_YEAR = 252
    TRADING_DAYS_PER_MONTH = 21
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_returns(
        self,
        portfolio_history: List[Dict]
    ) -> Tuple[float, float, float]:
        """计算收益率指标"""
        if len(portfolio_history) < 2:
            return 0.0, 0.0, 0.0
        
        initial_value = portfolio_history[0]['portfolio_value']
        final_value = portfolio_history[-1]['portfolio_value']
        total_return = (final_value - initial_value) / initial_value * 100
        
        num_days = len(portfolio_history)
        years = num_days / self.TRADING_DAYS_PER_YEAR
        if years > 0:
            annual_return = ((final_value / initial_value) ** (1 / years) - 1) * 100
        else:
            annual_return = 0.0
        
        months = num_days / self.TRADING_DAYS_PER_MONTH
        if months > 0:
            monthly_return = ((final_value / initial_value) ** (1 / months) - 1) * 100
        else:
            monthly_return = 0.0
        
        return total_return, annual_return, monthly_return
    
    def calculate_volatility(
        self,
        portfolio_history: List[Dict]
    ) -> float:
        """计算年化波动率"""
        if len(portfolio_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(portfolio_history)):
            prev = portfolio_history[i - 1]['portfolio_value']
            curr = portfolio_history[i]['portfolio_value']
            if prev > 0:
                ret = (curr - prev) / prev
                returns.append(ret)
        
        if len(returns) == 0:
            return 0.0
        
        returns = np.array(returns)
        daily_volatility = np.std(returns, ddof=1)
        annual_volatility = daily_volatility * np.sqrt(self.TRADING_DAYS_PER_YEAR)
        
        return annual_volatility * 100
    
    def calculate_max_drawdown(
        self,
        portfolio_history: List[Dict]
    ) -> float:
        """计算最大回撤"""
        if len(portfolio_history) == 0:
            return 0.0
        
        portfolio_values = [h['portfolio_value'] for h in portfolio_history]
        cummax = np.maximum.accumulate(portfolio_values)
        drawdowns = (cummax - portfolio_values) / cummax
        max_drawdown = np.max(drawdowns) * 100
        
        return max_drawdown
    
    def calculate_sharpe_ratio(
        self,
        annual_return: float,
        annual_volatility: float
    ) -> float:
        """计算夏普比率"""
        if annual_volatility == 0:
            return 0.0
        
        excess_return = annual_return - self.risk_free_rate * 100
        sharpe = excess_return / annual_volatility
        
        return sharpe
    
    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> float:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return 0.0
        
        calmar = annual_return / max_drawdown
        return calmar
    
    def calculate_sortino_ratio(
        self,
        portfolio_history: List[Dict],
        target_return: float = 0.0
    ) -> float:
        """计算索提诺比率"""
        if len(portfolio_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(portfolio_history)):
            prev = portfolio_history[i - 1]['portfolio_value']
            curr = portfolio_history[i]['portfolio_value']
            if prev > 0:
                ret = (curr - prev) / prev
                returns.append(ret)
        
        if len(returns) == 0:
            return 0.0
        
        returns = np.array(returns)
        
        downside_returns = returns[returns < target_return / self.TRADING_DAYS_PER_YEAR]
        if len(downside_returns) == 0:
            return 0.0
        
        downside_volatility = np.std(downside_returns, ddof=1)
        downside_volatility_annual = downside_volatility * np.sqrt(self.TRADING_DAYS_PER_YEAR)
        
        excess_return = np.mean(returns) * self.TRADING_DAYS_PER_YEAR - target_return
        
        if downside_volatility_annual == 0:
            return 0.0
        
        sortino = excess_return / downside_volatility_annual
        return sortino
    
    def calculate_win_rate(
        self,
        portfolio_history: List[Dict]
    ) -> float:
        """计算胜率"""
        if len(portfolio_history) < 2:
            return 0.0
        
        win_days = 0
        total_days = len(portfolio_history) - 1
        
        for i in range(1, len(portfolio_history)):
            prev = portfolio_history[i - 1]['portfolio_value']
            curr = portfolio_history[i]['portfolio_value']
            if curr > prev:
                win_days += 1
        
        if total_days == 0:
            return 0.0
        
        win_rate = win_days / total_days * 100
        return win_rate
    
    def calculate_turnover(
        self,
        portfolio_history: List[Dict],
        trades: List[Dict]
    ) -> float:
        """计算平均换手率"""
        if len(portfolio_history) == 0 or len(trades) == 0:
            return 0.0
        
        monthly_turnover = []
        
        df_trades = pd.DataFrame(trades)
        df_trades['date'] = pd.to_datetime(df_trades['date'])
        
        dates = [h['date'] for h in portfolio_history]
        current_month = None
        monthly_trades_value = 0
        avg_portfolio_value = 0
        
        for h in portfolio_history:
            date = h['date']
            portfolio_value = h['portfolio_value']
            
            month = date.strftime('%Y-%m')
            
            if current_month is None:
                current_month = month
                monthly_trades_value = 0
                avg_portfolio_value = portfolio_value
            elif month != current_month:
                if avg_portfolio_value > 0:
                    turnover = monthly_trades_value / avg_portfolio_value * 100
                    monthly_turnover.append(turnover)
                
                current_month = month
                monthly_trades_value = 0
                avg_portfolio_value = portfolio_value
            else:
                avg_portfolio_value = (avg_portfolio_value + portfolio_value) / 2
        
        if len(monthly_turnover) == 0:
            return 0.0
        
        avg_turnover = np.mean(monthly_turnover)
        return avg_turnover
    
    def calculate_rebalance_count(
        self,
        trades: List[Dict]
    ) -> int:
        """计算调仓次数"""
        if len(trades) == 0:
            return 0
        
        df_trades = pd.DataFrame(trades)
        rebalance_dates = df_trades['date'].unique()
        
        return len(rebalance_dates)
    
    def analyze(
        self,
        portfolio_history: List[Dict],
        trades: List[Dict] = None
    ) -> Dict:
        """完整绩效分析"""
        if len(portfolio_history) == 0:
            return {}
        
        start_date = portfolio_history[0]['date']
        end_date = portfolio_history[-1]['date']
        trading_days = len(portfolio_history)
        
        total_return, annual_return, monthly_return = self.calculate_returns(portfolio_history)
        
        volatility = self.calculate_volatility(portfolio_history)
        max_drawdown = self.calculate_max_drawdown(portfolio_history)
        
        sharpe = self.calculate_sharpe_ratio(annual_return, volatility)
        calmar = self.calculate_calmar_ratio(annual_return, max_drawdown)
        sortino = self.calculate_sortino_ratio(portfolio_history)
        
        win_rate = self.calculate_win_rate(portfolio_history)
        
        rebalance_count = self.calculate_rebalance_count(trades or [])
        turnover = self.calculate_turnover(portfolio_history, trades or [])
        trade_count = len(trades or [])
        
        results = {
            '回测期间': f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            '交易日数': trading_days,
            '调仓次数': rebalance_count,
            '总收益率': round(total_return, 2),
            '年化收益率': round(annual_return, 2),
            '月均收益率': round(monthly_return, 2),
            '年化波动率': round(volatility, 2),
            '最大回撤': round(max_drawdown, 2),
            '夏普比率': round(sharpe, 2),
            '卡玛比率': round(calmar, 2),
            '索提诺比率': round(sortino, 2),
            '日胜率': round(win_rate, 2),
            '总交易次数': trade_count,
            '平均换手率': round(turnover, 2),
        }
        
        return results
