"""
牛市高倍收益策略 - 核心框架
============================

策略组合：
1. 高Beta策略 - 进攻核心
2. 趋势追踪策略 - 捕捉趋势
3. 板块轮动策略 - 轮动红利
4. 成长股精选策略 - Alpha来源

Author: OpenClaw
Date: 2026-02-09
"""

from .modules.high_beta import HighBetaStrategy
from .modules.trend import TrendFollowingStrategy
from .modules.sector_rotation import SectorRotationStrategy
from .modules.growth import GrowthStockStrategy
from .backtest.backtest_engine import BacktestEngine
from .factors.factor_calculator import FactorCalculator
from .utils.market_stage import MarketStageDetector
from .utils.risk_manager import RiskManager
from .config import StrategyConfig, default_config

__version__ = "1.0.0"
__all__ = [
    'HighBetaStrategy',
    'TrendFollowingStrategy', 
    'SectorRotationStrategy',
    'GrowthStockStrategy',
    'BacktestEngine',
    'FactorCalculator',
    'MarketStageDetector',
    'RiskManager',
    'StrategyConfig',
    'default_config'
]
