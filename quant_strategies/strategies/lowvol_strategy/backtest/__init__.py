"""
低波动率策略 - 回测模块
========================

本模块提供低波动率策略的回测功能。

功能说明：
1. 策略回测：模拟策略的历史表现
2. 绩效分析：计算年化收益率、最大回撤、夏普比率等
3. 交易记录：记录每次调仓的详细信息

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

from .backtest_engine import LowVolBacktest
from .performance import PerformanceAnalyzer

__all__ = ['LowVolBacktest', 'PerformanceAnalyzer']
