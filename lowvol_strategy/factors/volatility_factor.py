"""
波动率因子计算模块
====================

本模块提供股票波动率因子的计算功能。

功能说明：
1. 计算日收益率标准差
2. 计算年化波动率
3. 计算波动率排名（同行业/全市场）

计算公式：
- 日收益率标准差: σ_daily = StdDev(r_1, r_2, ..., r_N)
- 年化波动率: σ_annual = σ_daily × √250

参数配置：
- 默认计算周期: 20个交易日
- 可选周期: 10日、20日、30日、60日

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import numpy as np
import pandas as pd
from typing import Union, Optional


class VolatilityFactor:
    """
    波动率因子计算类
    
    用于计算股票的年化波动率及其排名。
    波动率是低波策略的核心因子之一。
    
    属性:
        window: 计算周期（交易日）
        annualize: 是否年化
    """
    
    # 年化交易日数
    TRADING_DAYS_PER_YEAR = 250
    
    def __init__(self, window: int = 20, annualize: bool = True):
        """
        初始化波动率因子计算器
        
        Args:
            window: 计算周期（交易日），默认20日
            annualize: 是否年化，默认True
        """
        self.window = window
        self.annualize = annualize
    
    def calculate(self, prices: Union[pd.Series, np.ndarray]) -> float:
        """
        计算年化波动率
        
        Args:
            prices: 价格序列（收盘价或日收益率）
                   如果是收盘价序列，会先计算收益率
                   如果是收益率序列，直接计算标准差
        
        Returns:
            float: 年化波动率（%）
        """
        if len(prices) < 2:
            return np.nan
        
        # 判断输入是价格还是收益率
        if isinstance(prices, pd.Series):
            # 如果是价格序列（数值较小，收益率序列数值更小）
            if prices.mean() > 1:  # 假设价格序列均值大于1
                returns = prices.pct_change().dropna()
            else:
                returns = prices.dropna()
        else:
            prices = np.array(prices)
            if np.mean(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
            else:
                returns = prices
        
        # 计算日收益率标准差
        daily_std = np.std(returns, ddof=1)
        
        # 年化波动率
        if self.annualize:
            annual_volatility = daily_std * np.sqrt(self.TRADING_DAYS_PER_YEAR)
            return annual_volatility * 100  # 转换为百分比
        else:
            return daily_std * 100
    
    def calculate_from_returns(self, returns: Union[pd.Series, np.ndarray]) -> float:
        """
        直接从收益率序列计算波动率
        
        Args:
            returns: 日收益率序列
        
        Returns:
            float: 年化波动率（%）
        """
        if isinstance(returns, pd.Series):
            returns = returns.dropna().values
        else:
            returns = np.array(returns)
            returns = returns[~np.isnan(returns)]
        
        if len(returns) < 2:
            return np.nan
        
        daily_std = np.std(returns, ddof=1)
        
        if self.annualize:
            return daily_std * np.sqrt(self.TRADING_DAYS_PER_YEAR) * 100
        else:
            return daily_std * 100
    
    def calculate_rolling_volatility(
        self, 
        prices: pd.Series, 
        windows: list = None
    ) -> pd.DataFrame:
        """
        计算多周期滚动波动率
        
        Args:
            prices: 收盘价序列
            windows: 周期列表，默认[10, 20, 60]
        
        Returns:
            pd.DataFrame: 各周期波动率
        """
        if windows is None:
            windows = [10, 20, 60]
        
        # 计算日收益率
        returns = prices.pct_change()
        
        result = pd.DataFrame(index=prices.index)
        
        for window in windows:
            # 滚动计算标准差
            rolling_std = returns.rolling(window=window).std()
            
            # 年化
            if self.annualize:
                result[f'volatility_{window}d'] = rolling_std * np.sqrt(self.TRADING_DAYS_PER_YEAR) * 100
            else:
                result[f'volatility_{window}d'] = rolling_std * 100
        
        return result
    
    def calculate_rank(
        self, 
        volatility_series: pd.Series, 
        method: str = 'ascending'
    ) -> pd.Series:
        """
        计算波动率排名
        
        Args:
            volatility_series: 波动率序列
            method: 排名方法
                   'ascending': 升序（低波动排名靠前）
                   'descending': 降序（高波动排名靠前）
        
        Returns:
            pd.Series: 排名（1为最优）
        """
        if method == 'ascending':
            return volatility_series.rank(method='min', ascending=True)
        else:
            return volatility_series.rank(method='min', ascending=False)
    
    def filter_by_volatility(
        self, 
        volatility_series: pd.Series, 
        upper_limit: float = 30.0,
        quantile_threshold: float = None
    ) -> pd.Series:
        """
        根据波动率阈值筛选
        
        Args:
            volatility_series: 波动率序列
            upper_limit: 波动率上限（%）
            quantile_threshold: 分位数阈值（如0.3表示选择后30%的低波股票）
        
        Returns:
            pd.Series: 布尔筛选序列
        """
        if quantile_threshold is not None:
            threshold = volatility_series.quantile(quantile_threshold)
        else:
            threshold = upper_limit
        
        return volatility_series <= threshold
    
    def get_description(self) -> dict:
        """
        获取因子描述
        
        Returns:
            dict: 因子描述信息
        """
        return {
            '因子名称': '波动率因子',
            '英文名称': 'Volatility Factor',
            '计算方法': f'标准差窗口={self.window}日，年化因子=√{self.TRADING_DAYS_PER_YEAR}',
            '取值范围': '0% - 无上限，通常在10%-50%之间',
            '有效周期': '短中期',
            '低波策略应用': '波动率越低，得分越高（低波优先）'
        }


# 便捷函数
def calculate_volatility(
    prices: Union[pd.Series, np.ndarray], 
    window: int = 20
) -> float:
    """
    计算年化波动率（便捷函数）
    
    Args:
        prices: 价格序列
        window: 计算周期
    
    Returns:
        float: 年化波动率（%）
    """
    factor = VolatilityFactor(window=window)
    return factor.calculate(prices)


def calculate_rolling_volatility(
    prices: pd.Series, 
    windows: list = None
) -> pd.DataFrame:
    """
    计算多周期滚动波动率（便捷函数）
    """
    factor = VolatilityFactor()
    return factor.calculate_rolling_volatility(prices, windows)
