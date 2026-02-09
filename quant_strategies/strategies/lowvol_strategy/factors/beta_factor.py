"""
Beta因子计算模块
================

本模块提供Beta系数因子的计算功能。

功能说明：
1. 计算股票相对于市场的Beta系数
2. 计算Alpha（超额收益）
3. 计算Beta排名

计算公式：
- Beta = Cov(股票收益, 市场收益) / Var(市场收益)

参数配置：
- 默认计算周期: 60日
- 可选周期: 40日、60日、120日

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, Tuple


class BetaFactor:
    """
    Beta因子计算类
    
    用于计算股票相对于市场的Beta系数。
    Beta反映股票的系统性风险暴露。
    
    属性:
        window: 计算周期（交易日）
        benchmark_code: 市场基准代码
    """
    
    def __init__(self, window: int = 60, benchmark_code: str = 'sh.000001'):
        """
        初始化Beta因子计算器
        
        Args:
            window: 计算周期（交易日），默认60日
            benchmark_code: 市场基准代码，默认沪深300
        """
        self.window = window
        self.benchmark_code = benchmark_code
    
    def calculate_returns(
        self, 
        prices: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        计算收益率序列
        
        Args:
            prices: 价格序列
        
        Returns:
            pd.Series: 收益率序列
        """
        if isinstance(prices, np.ndarray):
            prices = pd.Series(prices)
        
        returns = prices.pct_change()
        return returns
    
    def calculate_beta(
        self, 
        stock_returns: Union[pd.Series, np.ndarray],
        benchmark_returns: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> pd.Series:
        """
        计算Beta系数（滚动）
        
        Args:
            stock_returns: 股票收益率序列
            benchmark_returns: 市场基准收益率序列
            window: 计算窗口
        
        Returns:
            pd.Series: Beta系数序列
        """
        if window is None:
            window = self.window
        
        if isinstance(stock_returns, np.ndarray):
            stock_returns = pd.Series(stock_returns)
        if isinstance(benchmark_returns, np.ndarray):
            benchmark_returns = pd.Series(benchmark_returns)
        
        # 对齐数据
        combined = pd.DataFrame({
            'stock': stock_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        # 计算协方差和方差
        rolling_cov = combined['stock'].rolling(window=window).cov(combined['benchmark'])
        rolling_var = combined['benchmark'].rolling(window=window).var()
        
        # Beta = Cov / Var
        beta = rolling_cov / rolling_var
        
        return beta
    
    def calculate_beta_latest(
        self, 
        stock_returns: Union[pd.Series, np.ndarray],
        benchmark_returns: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> float:
        """
        计算最新的Beta系数（用于实时选股）
        
        Args:
            stock_returns: 股票收益率序列
            benchmark_returns: 市场基准收益率序列
            window: 计算窗口
        
        Returns:
            float: 最新Beta系数
        """
        beta_series = self.calculate_beta(stock_returns, benchmark_returns, window)
        
        # 返回最新的非空值
        beta_series = beta_series.dropna()
        if len(beta_series) > 0:
            return float(beta_series.iloc[-1])
        return np.nan
    
    def calculate_alpha(
        self, 
        stock_returns: Union[pd.Series, np.ndarray],
        benchmark_returns: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> pd.Series:
        """
        计算Alpha（超额收益）
        
        Args:
            stock_returns: 股票收益率序列
            benchmark_returns: 市场基准收益率序列
            window: 计算窗口
        
        Returns:
            pd.Series: Alpha序列
        """
        if window is None:
            window = self.window
        
        beta = self.calculate_beta(stock_returns, benchmark_returns, window)
        
        if isinstance(stock_returns, np.ndarray):
            stock_returns = pd.Series(stock_returns)
        if isinstance(benchmark_returns, np.ndarray):
            benchmark_returns = pd.Series(benchmark_returns)
        
        # Alpha = 股票收益 - Beta × 市场收益
        alpha = stock_returns - beta * benchmark_returns
        
        return alpha
    
    def calculate_capm_metrics(
        self, 
        stock_returns: Union[pd.Series, np.ndarray],
        benchmark_returns: Union[pd.Series, np.ndarray],
        risk_free_rate: float = 0.02,
        window: int = None
    ) -> pd.DataFrame:
        """
        计算CAPM相关指标
        
        Args:
            stock_returns: 股票收益率序列
            benchmark_returns: 市场基准收益率序列
            risk_free_rate: 无风险利率（年化）
            window: 计算窗口
        
        Returns:
            pd.DataFrame: 包含Beta, Alpha, R-squared等指标
        """
        if window is None:
            window = self.window
        
        if isinstance(stock_returns, np.ndarray):
            stock_returns = pd.Series(stock_returns)
        if isinstance(benchmark_returns, np.ndarray):
            benchmark_returns = pd.Series(benchmark_returns)
        
        # 对齐数据
        combined = pd.DataFrame({
            'stock': stock_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        # 计算Beta
        cov = combined['stock'].rolling(window=window).cov(combined['benchmark'])
        var = combined['benchmark'].rolling(window=window).var()
        beta = cov / var
        
        # 计算Alpha（年化）
        daily_rf = risk_free_rate / 252
        alpha = (combined['stock'] - daily_rf) - beta * (combined['benchmark'] - daily_rf)
        alpha_annualized = alpha.rolling(window=window).mean() * 252
        
        # 计算R-squared
        stock_mean = combined['stock'].rolling(window=window).mean()
        benchmark_mean = combined['benchmark'].rolling(window=window).mean()
        
        ss_tot = ((combined['stock'] - stock_mean) ** 2).rolling(window=window).sum()
        ss_res = ((combined['stock'] - (beta * combined['benchmark'] + alpha)) ** 2).rolling(window=window).sum()
        r_squared = 1 - (ss_res / ss_tot)
        
        result = pd.DataFrame({
            'beta': beta,
            'alpha_daily': alpha,
            'alpha_annualized': alpha_annualized,
            'r_squared': r_squared
        })
        
        return result
    
    def calculate_rank(
        self, 
        beta_series: pd.Series, 
        method: str = 'ascending',
        upper_limit: float = 1.2
    ) -> pd.Series:
        """
        计算Beta排名
        
        Args:
            beta_series: Beta系数序列
            method: 排名方法
                   'ascending': 升序（低Beta排名靠前）
                   'descending': 降序（高Beta排名靠前）
            upper_limit: Beta上限
        
        Returns:
            pd.Series: 排名
        """
        # 将超过上限的Beta设为NaN（排除高Beta股票）
        filtered_beta = beta_series.copy()
        filtered_beta[filtered_beta > upper_limit] = np.nan
        
        if method == 'ascending':
            return filtered_beta.rank(method='min', ascending=True)
        else:
            return filtered_beta.rank(method='min', ascending=False)
    
    def filter_by_beta(
        self, 
        beta_series: pd.Series, 
        upper_limit: float = 1.2,
        lower_limit: float = 0.5
    ) -> pd.Series:
        """
        根据Beta阈值筛选
        
        Args:
            beta_series: Beta系数序列
            upper_limit: Beta上限
            lower_limit: Beta下限
        
        Returns:
            pd.Series: 布尔筛选序列
        """
        return (beta_series >= lower_limit) & (beta_series <= upper_limit)
    
    def get_description(self) -> dict:
        """
        获取因子描述
        
        Returns:
            dict: 因子描述信息
        """
        return {
            '因子名称': 'Beta因子',
            '英文名称': 'Beta Factor',
            '计算方法': f'Beta=Cov(股票收益,市场收益)/Var(市场收益)，窗口={self.window}日',
            '取值范围': '通常在0.5-1.5之间',
            '有效周期': '中长期',
            '低波策略应用': 'Beta越低，系统性风险暴露越小'
        }


# 便捷函数
def calculate_beta(
    stock_returns: Union[pd.Series, np.ndarray],
    benchmark_returns: Union[pd.Series, np.ndarray],
    window: int = 60
) -> pd.Series:
    """
    计算Beta系数（便捷函数）
    """
    factor = BetaFactor(window=window)
    return factor.calculate_beta(stock_returns, benchmark_returns)
