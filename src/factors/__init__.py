# -*- coding: utf-8 -*-
"""
因子模块包
包含各种选股因子：ROE、净利润趋势、毛利率等
"""

from .base import BaseFactor
from .factor_roe import FactorROE, FactorROETTM
from .factor_profit_trend import FactorProfitTrend, FactorYoY, FactorQoQ
from .factor_profit_margin import FactorProfitMargin
from .factor_cashflow import FactorCashflow, FactorCFOToNP
from .factor_gross_margin import FactorGrossMargin
from .factor_debt_ratio import FactorDebtRatio, FactorDebtToEquity
from .factor_revenue_volatility import FactorRevenueVolatility, FactorRevenueStability
from .factor_profit_volatility import FactorProfitVolatility

__all__ = [
    # Base
    'BaseFactor',
    
    # ROE
    'FactorROE',
    'FactorROETTM',
    
    # Profit
    'FactorProfitTrend',
    'FactorYoY',
    'FactorQoQ',
    'FactorProfitMargin',
    
    # Cashflow
    'FactorCashflow',
    'FactorCFOToNP',
    
    # Margin
    'FactorGrossMargin',
    
    # Debt
    'FactorDebtRatio',
    'FactorDebtToEquity',
    
    # Volatility
    'FactorRevenueVolatility',
    'FactorRevenueStability',
    'FactorProfitVolatility',
]
