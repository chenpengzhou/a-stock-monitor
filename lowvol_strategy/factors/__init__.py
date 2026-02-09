"""
低波动率策略 - 因子计算模块
============================

本模块提供低波动率策略所需的各种因子计算功能：
1. 波动率因子（年化波动率）
2. ATR因子（真实波幅）
3. Beta因子（市场风险系数）
4. 复合低波评分

核心假设：
- 低波动股票长期表现优于高波动股票
- 波动率越低，风险调整后收益越高

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

from .volatility_factor import VolatilityFactor
from .atr_factor import ATRFactor
from .beta_factor import BetaFactor
from .quality_factor import QualityFactor
from .composite_score import CompositeLowVolScore

__all__ = [
    'VolatilityFactor',
    'ATRFactor',
    'BetaFactor',
    'QualityFactor',
    'CompositeLowVolScore'
]
