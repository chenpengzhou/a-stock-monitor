#!/usr/bin/env python3
"""
LowVol 选股模块
"""

import pandas as pd
from typing import List
from factors import LowVolFactor
from config import LowVolConfig


class LowVolSelector:
    """低波选股器"""
    
    def __init__(self, config: Dict = None):
        """初始化"""
        self.config = LowVolConfig(config)
        self.factor = LowVolFactor()
    
    def select(self, data: pd.DataFrame, market_type: str = 'bear') -> List[str]:
        """
        选股
        
        Args:
            data: 股票数据
            market_type: 市场类型
        
        Returns:
            选中的股票代码
        """
        top_n = self.config.get('top_n', 30)
        
        selected = self.factor.select_stocks(
            data,
            top_n=top_n,
            market_type=market_type
        )
        
        return selected
    
    def get_position(self, market_type: str) -> float:
        """
        获取推荐仓位
        
        Args:
            market_type: 市场类型
        
        Returns:
            仓位比例
        """
        return self.config.get_position(market_type)


if __name__ == "__main__":
    print("LowVol Selector Module loaded")
    selector = LowVolSelector()
    print(f"Position (bear): {selector.get_position('bear')}")
    print(f"Position (neutral): {selector.get_position('neutral')}")
    print(f"Position (bull): {selector.get_position('bull')}")
