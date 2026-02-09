"""
低波动率策略主入口
==================

本模块提供低波动率策略的统一接口。

使用示例:
    from lowvol_strategy import LowVolStrategy
    
    # 初始化策略
    strategy = LowVolStrategy()
    
    # 运行回测
    results = strategy.backtest(start_date='2020-01-01', end_date='2024-12-31')
    
    # 打印结果
    strategy.print_results()

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

import pandas as pd

from .config import LowVolConfig
from .factors import (
    VolatilityFactor,
    ATRFactor,
    BetaFactor,
    QualityFactor,
    CompositeLowVolScore
)
from .selection import LowVolStockSelector
from .position import PositionManager
from .backtest import LowVolBacktest, PerformanceAnalyzer


class LowVolStrategy:
    """
    低波动率策略主类
    
    整合因子计算、选股、仓位管理和回测功能。
    
    示例:
        >>> strategy = LowVolStrategy()
        >>> strategy.load_data(data)
        >>> results = strategy.run_backtest()
    """
    
    def __init__(self, config: LowVolConfig = None):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config or LowVolConfig()
        
        # 初始化组件
        self.selector = LowVolStockSelector(self.config)
        self.position_manager = PositionManager(self.config)
        self.backtest = LowVolBacktest(self.config, self.selector, self.position_manager)
        
        # 数据存储
        self.data = None
    
    def load_data(self, data: pd.DataFrame):
        """
        加载数据
        
        Args:
            data: 股票因子数据
        """
        self.data = data.copy()
        self.backtest.load_data(data)
    
    def run_backtest(
        self,
        start_date: str = None,
        end_date: str = None,
        frequency: str = 'monthly'
    ):
        """
        运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            frequency: 调仓频率
        
        Returns:
            dict: 回测结果
        """
        # 转换日期格式
        start = pd.to_datetime(start_date) if start_date else None
        end = pd.to_datetime(end_date) if end_date else None
        
        results = self.backtest.run(start_date=start, end_date=end, frequency=frequency)
        
        return results
    
    def print_results(self):
        """打印回测结果"""
        self.backtest.print_results()
    
    def get_factor_description(self) -> dict:
        """
        获取因子描述
        
        Returns:
            dict: 各因子描述
        """
        return {
            '波动率因子': VolatilityFactor().get_description(),
            'ATR因子': ATRFactor().get_description(),
            'Beta因子': BetaFactor().get_description(),
            '质量因子': QualityFactor().get_description(),
            '复合评分': CompositeLowVolScore().get_description()
        }
    
    def get_strategy_info(self) -> dict:
        """
        获取策略信息
        
        Returns:
            dict: 策略信息
        """
        return {
            '策略名称': '低波动率策略',
            '英文名称': 'Low Volatility Strategy',
            '核心假设': '低波动股票长期表现优于高波动股票',
            '配置参数': self.config.to_dict(),
            '选股逻辑': self.selector.get_description(),
            '仓位管理': self.position_manager.get_description()
        }


# 便捷函数
def create_lowvol_strategy(config: LowVolConfig = None) -> LowVolStrategy:
    """
    创建低波动率策略实例（便捷函数）
    
    Args:
        config: 策略配置
    
    Returns:
        LowVolStrategy: 策略实例
    """
    return LowVolStrategy(config)


# 导出
__all__ = [
    'LowVolStrategy',
    'LowVolConfig',
    'VolatilityFactor',
    'ATRFactor',
    'BetaFactor',
    'QualityFactor',
    'CompositeLowVolScore',
    'LowVolStockSelector',
    'PositionManager',
    'LowVolBacktest',
    'PerformanceAnalyzer',
    'create_lowvol_strategy'
]
