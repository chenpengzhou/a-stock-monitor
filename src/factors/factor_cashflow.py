# -*- coding: utf-8 -*-
"""
现金流因子模块

经营性现金流/营收（CFO to Revenue）
衡量公司现金流质量。

方向：越高越好
"""

import pandas as pd
from typing import Dict, Optional
from .base import BaseFactor


class FactorCashflow(BaseFactor):
    """现金流/营收因子"""
    
    name = "CashflowToRevenue"
    description = "经营性现金流/营收，衡量现金流质量"
    direction = "higher"
    weight = 0.15  # 默认权重 15%
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算现金流/营收
        
        Args:
            stock_data: 包含 'CFOToOR' 列的 DataFrame
            
        Returns:
            现金流/营收 Series
        """
        if 'CFOToOR' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'CFOToOR' 列")
        
        cfo = stock_data['CFOToOR'].astype(float)
        
        # 处理无效值
        cfo = cfo.replace([float('inf'), float('-inf')], float('nan'))
        
        return cfo
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'CFOToOR' in stock_data.columns and stock_data['CFOToOR'].notna().any()


class FactorCFOToNP(BaseFactor):
    """现金流/净利润因子"""
    
    name = "CFOToNetProfit"
    description = "经营性现金流/净利润，衡量盈利质量"
    direction = "higher"
    weight = 0.10
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算现金流/净利润
        
        Args:
            stock_data: 包含 'CFOToNP' 列的 DataFrame
            
        Returns:
            现金流/净利润 Series
        """
        if 'CFOToNP' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'CFOToNP' 列")
        
        cfo_np = stock_data['CFOToNP'].astype(float)
        
        # 处理无效值
        cfo_np = cfo_np.replace([float('inf'), float('-inf')], float('nan'))
        
        return cfo_np
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'CFOToNP' in stock_data.columns and stock_data['CFOToNP'].notna().any()


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("现金流因子测试")
    print("=" * 60)
    
    test_data = pd.DataFrame({
        'code': ['sh.600519', 'sh.600036', 'sh.600000'],
        'CFOToOR': [0.72, 0.35, 0.28]  # 茅台72%, 招行35%, 浦发28%
    }).set_index('code')
    
    factor = FactorCashflow()
    
    print("\n原始数据:")
    print(test_data)
    
    print("\n现金流/营收:")
    print(factor.calculate(test_data))
    
    print("\n分数:")
    print(factor.transform(factor.calculate(test_data)))
    
    print("\n" + "=" * 60)
