#!/usr/bin/env python3
"""
LowVol 低波动策略

低波动防守策略 - 熊市专用

策略定位:
- 熊市: 主力防守，减少亏损
- 震荡市: 稳健配置
- 牛市: 降低仓位

核心因子:
- 波动率 (40%)
- ATR (25%)
- Beta (20%)
- 质量 (15%)
"""

__version__ = "1.0"
__author__ = "Quant Team"

from factors import VolatilityFactor, ATRFactor, BetaFactor, QualityFactor, LowVolFactor
from backtest import LowVolBacktest
from config import LowVolConfig
from selection import LowVolSelector
from position import LowVolPositionManager


__all__ = [
    'VolatilityFactor',
    'ATRFactor',
    'BetaFactor',
    'QualityFactor',
    'LowVolFactor',
    'LowVolBacktest',
    'LowVolConfig',
    'LowVolSelector',
    'LowVolPositionManager',
]


if __name__ == "__main__":
    print(f"LowVol Strategy v{__version__}")
    print("LowVol Factor weights: vol=40%, atr=25%, beta=20%, quality=15%")
    print("\nMarket positions:")
    print("  Bear: 40%")
    print("  Neutral: 20%")
    print("  Bull: 0%")
