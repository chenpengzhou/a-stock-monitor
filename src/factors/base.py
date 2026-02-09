# -*- coding: utf-8 -*-
"""
因子基类
所有因子模块的父类，定义统一的接口规范
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseFactor(ABC):
    """因子基类"""
    
    # 因子元信息（子类覆盖）
    name: str = "base_factor"
    description: str = ""
    direction: str = "higher"  # "higher"=越高越好, "lower"=越低越好
    weight: float = 1.0  # 默认权重
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化因子
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        pass
    
    @abstractmethod
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算因子值
        
        Args:
            stock_data: 股票数据 DataFrame
            
        Returns:
            因子值 Series（index为股票代码）
        """
        pass
    
    def transform(self, factor_values: pd.Series) -> pd.Series:
        """
        因子值转换：Winsorize + 分位数排名
        
        Args:
            factor_values: 原始因子值
            
        Returns:
            转换后的因子分数（1-10分）
        """
        from ..utils import winsorize, rank_to_score
        
        # Winsorize 极端值
        winsorized = winsorize(factor_values)
        
        # 分位数排名
        if self.direction == "higher":
            scores = rank_to_score(winsorized, bins=10, higher_is_better=True)
        else:
            scores = rank_to_score(winsorized, bins=10, higher_is_better=False)
        
        return scores
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """
        验证数据是否满足因子计算要求
        
        Args:
            stock_data: 股票数据
            
        Returns:
            True=数据可用
        """
        return not stock_data.empty
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取因子信息
        
        Returns:
            因子信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "direction": self.direction,
            "weight": self.weight,
        }
    
    def run(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        完整运行：计算 + 转换
        
        Args:
            stock_data: 股票数据
            
        Returns:
            因子分数 Series（1-10分）
        """
        if not self.validate(stock_data):
            raise ValueError("数据验证失败")
        
        factor_values = self.calculate(stock_data)
        scores = self.transform(factor_values)
        
        return scores
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', direction='{self.direction}')"


class DirectionMixin:
    """方向混合类"""
    
    def is_higher_better(self) -> bool:
        """是否越高越好"""
        return self.direction == "higher"
    
    def is_lower_better(self) -> bool:
        """是否越低越好"""
        return self.direction == "lower"


# ===== 测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("因子基类测试")
    print("=" * 60)
    
    class DummyFactor(BaseFactor):
        name = "dummy"
        direction = "higher"
        
        def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
            return pd.Series(1.0, index=stock_data.index)
    
    factor = DummyFactor()
    print(f"因子信息: {factor.get_info()}")
    print(f"repr: {factor}")
    
    print("\n" + "=" * 60)
