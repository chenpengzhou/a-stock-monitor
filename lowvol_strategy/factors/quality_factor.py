"""
质量因子计算模块
================

本模块提供质量因子的计算功能，用于辅助低波选股。

功能说明：
1. ROE因子（净资产收益率）
2. 资产负债率因子
3. 股息率因子
4. 综合质量评分

参数配置参考产品设计文档：
- ROE > 5%
- 资产负债率 < 70%
- 股息率 > 0.5%

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import numpy as np
import pandas as pd
from typing import Union, Dict, Optional


class QualityFactor:
    """
    质量因子计算类
    
    用于计算股票的质量指标。
    质量因子用于排除基本面恶化的低波股票（低波陷阱）。
    
    属性:
        min_roe: 最低ROE阈值
        max_debt_ratio: 最高资产负债率阈值
        min_dividend_yield: 最低股息率阈值
    """
    
    def __init__(
        self, 
        min_roe: float = 5.0,
        max_debt_ratio: float = 70.0,
        min_dividend_yield: float = 0.5
    ):
        """
        初始化质量因子计算器
        
        Args:
            min_roe: 最低ROE（%），默认5%
            max_debt_ratio: 最高资产负债率（%），默认70%
            min_dividend_yield: 最低股息率（%），默认0.5%
        """
        self.min_roe = min_roe
        self.max_debt_ratio = max_debt_ratio
        self.min_dividend_yield = min_dividend_yield
    
    def calculate_roe_score(self, roe_series: pd.Series) -> pd.Series:
        """
        计算ROE得分
        
        Args:
            roe_series: ROE序列（%）
        
        Returns:
            pd.Series: ROE得分（越高越好）
        """
        # ROE标准化到0-1区间
        roe_normalized = (roe_series - roe_series.min()) / (roe_series.max() - roe_series.min() + 1e-8)
        return roe_normalized
    
    def calculate_debt_ratio_score(self, debt_ratio_series: pd.Series) -> pd.Series:
        """
        计算资产负债率得分（越低越好）
        
        Args:
            debt_ratio_series: 资产负债率序列（%）
        
        Returns:
            pd.Series: 得分（越低得分越高）
        """
        # 资产负债率标准化（反转）
        debt_normalized = (debt_ratio_series.max() - debt_ratio_series) / (debt_ratio_series.max() - debt_ratio_series.min() + 1e-8)
        return debt_normalized
    
    def calculate_dividend_yield_score(self, dividend_series: pd.Series) -> pd.Series:
        """
        计算股息率得分
        
        Args:
            dividend_series: 股息率序列（%）
        
        Returns:
            pd.Series: 得分（越高越好）
        """
        # 股息率标准化
        div_normalized = (dividend_series - dividend_series.min()) / (dividend_series.max() - dividend_series.min() + 1e-8)
        return div_normalized
    
    def calculate_composite_quality_score(
        self,
        roe_series: pd.Series,
        debt_ratio_series: pd.Series,
        dividend_series: pd.Series,
        weights: Dict[str, float] = None
    ) -> pd.Series:
        """
        计算综合质量得分
        
        Args:
            roe_series: ROE序列（%）
            debt_ratio_series: 资产负债率序列（%）
            dividend_series: 股息率序列（%）
            weights: 各因子权重
        
        Returns:
            pd.Series: 综合质量得分（越高越好）
        """
        if weights is None:
            weights = {
                'roe': 0.4,
                'debt_ratio': 0.3,
                'dividend': 0.3
            }
        
        # 计算各因子得分
        roe_score = self.calculate_roe_score(roe_series)
        debt_score = self.calculate_debt_ratio_score(debt_ratio_series)
        dividend_score = self.calculate_dividend_yield_score(dividend_series)
        
        # 加权综合得分
        quality_score = (
            weights['roe'] * roe_score +
            weights['debt_ratio'] * debt_score +
            weights['dividend'] * dividend_score
        )
        
        return quality_score
    
    def filter_by_quality(
        self,
        roe_series: pd.Series,
        debt_ratio_series: pd.Series,
        dividend_series: pd.Series,
        min_roe: float = None,
        max_debt_ratio: float = None,
        min_dividend_yield: float = None
    ) -> pd.Series:
        """
        根据质量阈值筛选
        
        Args:
            roe_series: ROE序列（%）
            debt_ratio_series: 资产负债率序列（%）
            dividend_series: 股息率序列（%）
            min_roe: 最低ROE
            max_debt_ratio: 最高资产负债率
            min_dividend_yield: 最低股息率
        
        Returns:
            pd.Series: 布尔筛选序列
        """
        if min_roe is None:
            min_roe = self.min_roe
        if max_debt_ratio is None:
            max_debt_ratio = self.max_debt_ratio
        if min_dividend_yield is None:
            min_dividend_yield = self.min_dividend_yield
        
        roe_filter = roe_series >= min_roe
        debt_filter = debt_ratio_series <= max_debt_ratio
        dividend_filter = dividend_series >= min_dividend_yield
        
        return roe_filter & debt_filter & dividend_filter
    
    def get_description(self) -> dict:
        """
        获取因子描述
        
        Returns:
            dict: 因子描述信息
        """
        return {
            '因子名称': '质量因子',
            '英文名称': 'Quality Factor',
            '包含指标': 'ROE、资产负债率、股息率',
            '筛选条件': f'ROE>{self.min_roe}%, 资产负债率<{self.max_debt_ratio}%, 股息率>{self.min_dividend_yield}%',
            '低波策略应用': '排除基本面恶化的低波股票，避免低波陷阱'
        }


# 便捷函数
def calculate_quality_score(
    roe_series: pd.Series,
    debt_ratio_series: pd.Series,
    dividend_series: pd.Series
) -> pd.Series:
    """
    计算综合质量得分（便捷函数）
    """
    factor = QualityFactor()
    return factor.calculate_composite_quality_score(roe_series, debt_ratio_series, dividend_series)
