"""
复合低波评分模块
================

本模块提供复合低波评分计算功能。

功能说明：
1. 综合波动率、ATR%、Beta、质量因子计算复合得分
2. 支持自定义因子权重
3. 支持行业中性化处理

计算公式：
低波综合得分 = w1 × 波动率排名 + w2 × ATR%排名 + w3 × Beta排名 + w4 × 质量因子得分

默认权重（产品设计文档）：
- 波动率排名: 0.35
- ATR%排名: 0.25
- Beta排名: 0.20
- 质量因子: 0.20

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Union
from .volatility_factor import VolatilityFactor
from .atr_factor import ATRFactor
from .beta_factor import BetaFactor
from .quality_factor import QualityFactor


class CompositeLowVolScore:
    """
    复合低波评分计算类
    
    用于计算综合低波评分，评分越低表示波动率特征越优。
    
    属性:
        volatility_weight: 波动率排名权重
        atr_weight: ATR%排名权重
        beta_weight: Beta排名权重
        quality_weight: 质量因子权重
    """
    
    # 默认因子权重（来自产品设计文档）
    DEFAULT_WEIGHTS = {
        'volatility': 0.35,
        'atr': 0.25,
        'beta': 0.20,
        'quality': 0.20
    }
    
    def __init__(
        self,
        volatility_weight: float = 0.35,
        atr_weight: float = 0.25,
        beta_weight: float = 0.20,
        quality_weight: float = 0.20,
        enable_industry_neutral: bool = True
    ):
        """
        初始化复合低波评分计算器
        
        Args:
            volatility_weight: 波动率排名权重
            atr_weight: ATR%排名权重
            beta_weight: Beta排名权重
            quality_weight: 质量因子权重
            enable_industry_neutral: 是否启用行业中性化
        """
        self.volatility_weight = volatility_weight
        self.atr_weight = atr_weight
        self.beta_weight = beta_weight
        self.quality_weight = quality_weight
        self.enable_industry_neutral = enable_industry_neutral
        
        # 验证权重之和为1
        total_weight = (
            self.volatility_weight + 
            self.atr_weight + 
            self.beta_weight + 
            self.quality_weight
        )
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"因子权重之和必须为1.0，当前为{total_weight}")
    
    def calculate_zscore(self, series: pd.Series) -> pd.Series:
        """
        计算Z-Score标准化
        
        Args:
            series: 原始序列
        
        Returns:
            pd.Series: Z-Score标准化序列
        """
        mean = series.mean()
        std = series.std()
        
        if std == 0 or pd.isna(std):
            return pd.Series(0, index=series.index)
        
        return (series - mean) / std
    
    def calculate_rank(self, series: pd.Series, ascending: bool = True) -> pd.Series:
        """
        计算排名并归一化到0-1
        
        Args:
            series: 原始序列
            ascending: 升序排名
        
        Returns:
            pd.Series: 归一化排名（0-1之间）
        """
        rank = series.rank(method='average', ascending=ascending)
        rank_normalized = (rank - rank.min()) / (rank.max() - rank.min() + 1e-8)
        return rank_normalized
    
    def calculate_industry_neutral(
        self, 
        factor_series: pd.Series,
        industry_series: pd.Series
    ) -> pd.Series:
        """
        行业中性化处理
        
        Args:
            factor_series: 因子序列
            industry_series: 行业序列
        
        Returns:
            pd.Series: 行业中性化后的因子值
        """
        if not self.enable_industry_neutral:
            return factor_series
        
        # 按行业分组，计算行业中位数
        industry_median = factor_series.groupby(industry_series).transform('median')
        
        # 中性化：因子值 - 行业中位数
        neutralized = factor_series - industry_median
        
        return neutralized
    
    def calculate(
        self,
        volatility: Union[pd.Series, float],
        atr_percent: Union[pd.Series, float],
        beta: Union[pd.Series, float],
        quality: Union[pd.Series, float],
        industry: pd.Series = None,
        normalize: bool = True
    ) -> Union[pd.Series, float]:
        """
        计算复合低波评分
        
        Args:
            volatility: 波动率（%），越低越好
            atr_percent: ATR百分比（%），越低越好
            beta: Beta系数，越低越好
            quality: 质量得分，越高越好
            industry: 行业序列（可选，用于行业中性化）
            normalize: 是否标准化
        
        Returns:
            pd.Series/float: 复合低波评分（越低越好）
        """
        # 处理单个值
        is_single_value = not isinstance(volatility, pd.Series)
        
        if is_single_value:
            volatility = pd.Series([volatility])
            atr_percent = pd.Series([atr_percent])
            beta = pd.Series([beta])
            quality = pd.Series([quality])
            if industry is not None:
                industry = pd.Series([industry])
        
        # 排名标准化（0-1之间，越低越好）
        vol_rank = self.calculate_rank(volatility, ascending=True)
        atr_rank = self.calculate_rank(atr_percent, ascending=True)
        beta_rank = self.calculate_rank(beta, ascending=True)
        
        # 质量因子已经是越高越好，不需要反转
        quality_rank = self.calculate_rank(quality, ascending=False)
        
        # 行业中性化（如果提供了行业信息）
        if industry is not None:
            vol_rank = self.calculate_industry_neutral(vol_rank, industry)
            atr_rank = self.calculate_industry_neutral(atr_rank, industry)
            beta_rank = self.calculate_industry_neutral(beta_rank, industry)
            quality_rank = self.calculate_industry_neutral(quality_rank, industry)
        
        # 标准化
        if normalize:
            vol_rank = self.calculate_zscore(vol_rank)
            atr_rank = self.calculate_zscore(atr_rank)
            beta_rank = self.calculate_zscore(beta_rank)
            quality_rank = self.calculate_zscore(quality_rank)
        
        # 加权综合得分
        composite_score = (
            self.volatility_weight * vol_rank +
            self.atr_weight * atr_rank +
            self.beta_weight * beta_rank +
            self.quality_weight * quality_rank
        )
        
        if is_single_value:
            return float(composite_score.iloc[0])
        return composite_score
    
    def calculate_dataframe(
        self,
        df: pd.DataFrame,
        volatility_col: str = 'volatility',
        atr_percent_col: str = 'atr_percent',
        beta_col: str = 'beta',
        quality_col: str = 'quality_score',
        industry_col: str = 'industry'
    ) -> pd.DataFrame:
        """
        从DataFrame计算复合低波评分
        
        Args:
            df: 包含因子的DataFrame
            volatility_col: 波动率列名
            atr_percent_col: ATR百分比列名
            beta_col: Beta列名
            quality_col: 质量得分列名
            industry_col: 行业列名
        
        Returns:
            pd.DataFrame: 添加了composite_score列的DataFrame
        """
        result = df.copy()
        
        industry = None
        if industry_col in df.columns and self.enable_industry_neutral:
            industry = df[industry_col]
        
        result['composite_score'] = self.calculate(
            volatility=df[volatility_col],
            atr_percent=df[atr_percent_col],
            beta=df[beta_col],
            quality=df[quality_col],
            industry=industry
        )
        
        return result
    
    def select_top_stocks(
        self,
        composite_scores: pd.Series,
        top_n: int = 30,
        ascending: bool = True
    ) -> pd.Index:
        """
        选择Top N低波股票
        
        Args:
            composite_scores: 复合低波评分序列
            top_n: 选择数量
            ascending: 是否升序（低分优先）
        
        Returns:
            pd.Index: 选中的股票代码
        """
        sorted_scores = composite_scores.sort_values(ascending=ascending)
        selected = sorted_scores.head(top_n).index
        return selected
    
    def get_description(self) -> dict:
        """
        获取评分模型描述
        
        Returns:
            dict: 描述信息
        """
        return {
            '模型名称': '复合低波评分模型',
            '英文名称': 'Composite Low Volatility Score Model',
            '因子权重': {
                '波动率排名': self.volatility_weight,
                'ATR%排名': self.atr_weight,
                'Beta排名': self.beta_weight,
                '质量因子': self.quality_weight
            },
            '评分规则': '综合得分越低，低波特征越明显',
            '行业中性化': self.enable_industry_neutral
        }


# 便捷函数
def calculate_composite_lowvol_score(
    volatility: Union[pd.Series, float],
    atr_percent: Union[pd.Series, float],
    beta: Union[pd.Series, float],
    quality: Union[pd.Series, float],
    volatility_weight: float = 0.35,
    atr_weight: float = 0.25,
    beta_weight: float = 0.20,
    quality_weight: float = 0.20
) -> Union[pd.Series, float]:
    """
    计算复合低波评分（便捷函数）
    """
    scorer = CompositeLowVolScore(
        volatility_weight=volatility_weight,
        atr_weight=atr_weight,
        beta_weight=beta_weight,
        quality_weight=quality_weight
    )
    return scorer.calculate(volatility, atr_percent, beta, quality)
