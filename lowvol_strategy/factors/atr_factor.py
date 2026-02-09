"""
ATR因子计算模块
================

本模块提供ATR（Average True Range，平均真实波幅）因子的计算功能。

功能说明：
1. 计算真实波幅（True Range）
2. 计算ATR及ATR百分比
3. 计算ATR排名

计算公式：
- TrueRange = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
- ATR = Mean(TrueRange, N)
- ATR% = ATR / Close × 100%

参数配置：
- 默认计算周期: 14日
- 可选周期: 10日、14日、20日

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import numpy as np
import pandas as pd
from typing import Union, Optional


class ATRFactor:
    """
    ATR因子计算类
    
    用于计算股票的ATR及ATR百分比。
    ATR反映股票的真实波动幅度，不受方向影响。
    
    属性:
        window: ATR计算周期（交易日）
    """
    
    def __init__(self, window: int = 14):
        """
        初始化ATR因子计算器
        
        Args:
            window: 计算周期（交易日），默认14日
        """
        self.window = window
    
    def calculate_true_range(
        self, 
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        计算真实波幅（True Range）
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
        
        Returns:
            pd.Series: 真实波幅序列
        """
        # 转换为pandas Series（如果需要）
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        
        # 前一日收盘价
        prev_close = close.shift(1)
        
        # 计算三种波幅
        tr1 = high - low                          # 当日最高价-最低价
        tr2 = np.abs(high - prev_close)           # 当日最高价-前一日收盘价
        tr3 = np.abs(low - prev_close)            # 当日最低价-前一日收盘价
        
        # 取三者最大值
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        return true_range
    
    def calculate_atr(
        self, 
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> pd.Series:
        """
        计算ATR（平均真实波幅）
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算周期
        
        Returns:
            pd.Series: ATR序列
        """
        if window is None:
            window = self.window
        
        true_range = self.calculate_true_range(high, low, close)
        atr = true_range.rolling(window=window).mean()
        
        return atr
    
    def calculate_atr_percent(
        self, 
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> pd.Series:
        """
        计算ATR百分比（归一化的波动指标）
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算周期
        
        Returns:
            pd.Series: ATR百分比序列（%）
        """
        if window is None:
            window = self.window
        
        atr = self.calculate_atr(high, low, close, window)
        atr_percent = (atr / close) * 100
        
        return atr_percent
    
    def calculate_atr_percent_latest(
        self, 
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        window: int = None
    ) -> float:
        """
        计算最新的ATR百分比（用于实时选股）
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算周期
        
        Returns:
            float: 最新ATR百分比（%）
        """
        atr_percent = self.calculate_atr_percent(high, low, close, window)
        
        # 返回最新的非空值
        atr_percent = atr_percent.dropna()
        if len(atr_percent) > 0:
            return float(atr_percent.iloc[-1])
        return np.nan
    
    def calculate_rank(
        self, 
        atr_percent_series: pd.Series, 
        method: str = 'ascending'
    ) -> pd.Series:
        """
        计算ATR百分比排名
        
        Args:
            atr_percent_series: ATR百分比序列
            method: 排名方法
                   'ascending': 升序（低ATR排名靠前）
                   'descending': 降序（高ATR排名靠前）
        
        Returns:
            pd.Series: 排名
        """
        if method == 'ascending':
            return atr_percent_series.rank(method='min', ascending=True)
        else:
            return atr_percent_series.rank(method='min', ascending=False)
    
    def filter_by_atr(
        self, 
        atr_percent_series: pd.Series, 
        upper_limit: float = 5.0,
        quantile_threshold: float = None
    ) -> pd.Series:
        """
        根据ATR百分比阈值筛选
        
        Args:
            atr_percent_series: ATR百分比序列
            upper_limit: ATR百分比上限（%）
            quantile_threshold: 分位数阈值
        
        Returns:
            pd.Series: 布尔筛选序列
        """
        if quantile_threshold is not None:
            threshold = atr_percent_series.quantile(quantile_threshold)
        else:
            threshold = upper_limit
        
        return atr_percent_series <= threshold
    
    def get_description(self) -> dict:
        """
        获取因子描述
        
        Returns:
            dict: 因子描述信息
        """
        return {
            '因子名称': 'ATR因子',
            '英文名称': 'Average True Range Factor',
            '计算方法': f'TR=max(High-Low,|High-PrevClose|,|Low-PrevClose|)，ATR=Mean(TR,{self.window})',
            '取值范围': 'ATR%: 通常在1%-10%之间',
            '有效周期': '短中期',
            '低波策略应用': 'ATR%越低，得分越高（低波动优先）'
        }


# 便捷函数
def calculate_atr(
    high: Union[pd.Series, np.ndarray],
    low: Union[pd.Series, np.ndarray],
    close: Union[pd.Series, np.ndarray],
    window: int = 14
) -> pd.Series:
    """
    计算ATR（便捷函数）
    """
    factor = ATRFactor(window=window)
    return factor.calculate_atr(high, low, close)


def calculate_atr_percent(
    high: Union[pd.Series, np.ndarray],
    low: Union[pd.Series, np.ndarray],
    close: Union[pd.Series, np.ndarray],
    window: int = 14
) -> pd.Series:
    """
    计算ATR百分比（便捷函数）
    """
    factor = ATRFactor(window=window)
    return factor.calculate_atr_percent(high, low, close)
