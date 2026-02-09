"""
低波动率股票筛选器
==================

本模块提供完整的低波动率股票筛选逻辑。

选股流程：
1. 基础筛选（流动性、上市时间）
2. 财务筛选（ROE、资产负债率、股息率）
3. 低波筛选（波动率、Beta、ATR）
4. 低波评分（复合评分）
5. 最终选股（Top N）

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Union

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.lowvol_config import LowVolConfig
from factors import (
    VolatilityFactor,
    ATRFactor,
    BetaFactor,
    QualityFactor,
    CompositeLowVolScore
)


class LowVolStockSelector:
    """
    低波动率股票筛选器
    
    整合所有筛选条件，执行完整的选股流程。
    
    示例:
        >>> selector = LowVolStockSelector()
        >>> selected = selector.select(
        ...     stock_data=all_stocks_data,
        ...     trading_date='2026-01-31'
        ... )
        >>> print(f"选中{len(selected)}只低波股票")
    """
    
    def __init__(self, config: LowVolConfig = None):
        """
        初始化选股器
        
        Args:
            config: 策略配置，如果为None则使用默认配置
        """
        self.config = config or LowVolConfig()
        
        # 初始化因子计算器
        self.volatility_factor = VolatilityFactor(
            window=self.config.VOLATILITY_WINDOW
        )
        self.atr_factor = ATRFactor(
            window=self.config.ATR_WINDOW
        )
        self.beta_factor = BetaFactor(
            window=self.config.BETA_WINDOW,
            benchmark_code=self.config.BENCHMARK_CODE
        )
        self.quality_factor = QualityFactor(
            min_roe=self.config.MIN_ROE,
            max_debt_ratio=self.config.MAX_DEBT_RATIO,
            min_dividend_yield=self.config.MIN_DIVIDEND_YIELD
        )
        self.composite_scorer = CompositeLowVolScore(
            volatility_weight=self.config.VOLATILITY_WEIGHT,
            atr_weight=self.config.ATR_WEIGHT,
            beta_weight=self.config.BETA_WEIGHT,
            quality_weight=self.config.QUALITY_WEIGHT,
            enable_industry_neutral=self.config.ENABLE_INDUSTRY_NEUTRAL
        )
    
    def filter_basic(
        self,
        stock_data: pd.DataFrame,
        listing_days_col: str = 'listing_days',
        avg_turnover_col: str = 'avg_turnover',
        min_listing_days: int = None,
        min_avg_turnover: float = None
    ) -> pd.Series:
        """
        基础筛选（流动性和上市时间）
        
        Args:
            stock_data: 股票数据DataFrame
            listing_days_col: 上市天数列名
            avg_turnover_col: 日均成交额列名
            min_listing_days: 最低上市天数
            min_avg_turnover: 最低日均成交额（万元）
        
        Returns:
            pd.Series: 布尔筛选结果
        """
        if min_listing_days is None:
            min_listing_days = self.config.MIN_LISTING_DAYS
        if min_avg_turnover is None:
            min_avg_turnover = self.config.MIN_AVG_TURNOVER
        
        listing_filter = stock_data[listing_days_col] >= min_listing_days
        turnover_filter = stock_data[avg_turnover_col] >= min_avg_turnover
        
        return listing_filter & turnover_filter
    
    def filter_financial(
        self,
        stock_data: pd.DataFrame,
        roe_col: str = 'roe',
        debt_ratio_col: str = 'debt_ratio',
        dividend_yield_col: str = 'dividend_yield',
        min_roe: float = None,
        max_debt_ratio: float = None,
        min_dividend_yield: float = None
    ) -> pd.Series:
        """
        财务筛选（ROE、资产负债率、股息率）
        """
        if min_roe is None:
            min_roe = self.config.MIN_ROE
        if max_debt_ratio is None:
            max_debt_ratio = self.config.MAX_DEBT_RATIO
        if min_dividend_yield is None:
            min_dividend_yield = self.config.MIN_DIVIDEND_YIELD
        
        roe_filter = stock_data[roe_col] >= min_roe
        debt_filter = stock_data[debt_ratio_col] <= max_debt_ratio
        dividend_filter = stock_data[dividend_yield_col] >= min_dividend_yield
        
        return roe_filter & debt_filter & dividend_filter
    
    def filter_lowvol(
        self,
        stock_data: pd.DataFrame,
        volatility_col: str = 'volatility',
        beta_col: str = 'beta',
        atr_percent_col: str = 'atr_percent',
        volatility_upper_limit: float = None,
        beta_upper_limit: float = None,
        atr_percent_upper_limit: float = None
    ) -> pd.Series:
        """
        低波动筛选（波动率、Beta、ATR）
        """
        if volatility_upper_limit is None:
            volatility_upper_limit = self.config.VOLATILITY_UPPER_LIMIT
        if beta_upper_limit is None:
            beta_upper_limit = self.config.BETA_UPPER_LIMIT
        if atr_percent_upper_limit is None:
            atr_percent_upper_limit = None
        
        vol_filter = stock_data[volatility_col] <= volatility_upper_limit
        beta_filter = stock_data[beta_col] <= beta_upper_limit
        
        if atr_percent_upper_limit:
            atr_filter = stock_data[atr_percent_col] <= atr_percent_upper_limit
        else:
            atr_percent_upper_limit = stock_data[atr_percent_col].median()
            atr_filter = stock_data[atr_percent_col] <= atr_percent_upper_limit
        
        return vol_filter & beta_filter & atr_filter
    
    def calculate_scores(
        self,
        stock_data: pd.DataFrame,
        volatility_col: str = 'volatility',
        atr_percent_col: str = 'atr_percent',
        beta_col: str = 'beta',
        quality_col: str = 'quality_score',
        industry_col: str = 'industry'
    ) -> pd.DataFrame:
        """
        计算复合低波评分
        """
        industry = None
        if industry_col in stock_data.columns:
            industry = stock_data[industry_col]
        
        stock_data = self.composite_scorer.calculate_dataframe(
            df=stock_data,
            volatility_col=volatility_col,
            atr_percent_col=atr_percent_col,
            beta_col=beta_col,
            quality_col=quality_col,
            industry_col=industry_col if self.config.ENABLE_INDUSTRY_NEUTRAL else None
        )
        
        return stock_data
    
    def select(
        self,
        stock_data: pd.DataFrame,
        top_n: int = None,
        return_details: bool = False
    ) -> Union[pd.Series, Tuple[pd.Series, pd.DataFrame]]:
        """
        执行完整选股流程
        """
        if top_n is None:
            top_n = self.config.TOP_N_HOLDINGS
        
        df = stock_data.copy()
        
        # Step 1: 基础筛选
        basic_filter = self.filter_basic(df)
        df_step1 = df[basic_filter].copy()
        
        # Step 2: 财务筛选
        financial_filter = self.filter_financial(df_step1)
        df_step2 = df_step1[financial_filter].copy()
        
        # Step 3: 低波筛选
        lowvol_filter = self.filter_lowvol(df_step2)
        df_step3 = df_step2[lowvol_filter].copy()
        
        # Step 4: 计算复合评分
        df_scored = self.calculate_scores(df_step3)
        
        # Step 5: 按评分排序，选取Top N
        if len(df_scored) == 0:
            final_selection = pd.Series(False, index=df.index)
            details = pd.DataFrame()
        else:
            df_sorted = df_scored.sort_values('composite_score', ascending=True)
            top_stocks = df_sorted.head(top_n).index
            final_selection = pd.Series(False, index=df.index)
            final_selection.loc[top_stocks] = True
            details = df_sorted[['composite_score', 'volatility', 'beta', 'atr_percent', 'quality_score']].head(top_n)
        
        if return_details:
            return final_selection, details
        else:
            return final_selection
    
    def get_filter_summary(
        self,
        stock_data: pd.DataFrame
    ) -> Dict[str, int]:
        """
        获取各筛选步骤的股票数量
        """
        df = stock_data.copy()
        
        basic = self.filter_basic(df)
        df1 = df[basic]
        
        financial = self.filter_financial(df1)
        df2 = df1[financial]
        
        lowvol = self.filter_lowvol(df2)
        df3 = df2[lowvol]
        
        return {
            '原始数量': len(df),
            '基础筛选后': len(df1),
            '财务筛选后': len(df2),
            '低波筛选后': len(df3)
        }
