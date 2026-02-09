# -*- coding: utf-8 -*-
"""
负债率因子模块

负债率（Debt to Asset Ratio）
衡量公司的财务杠杆和偿债能力。

方向：越低越好
"""

import pandas as pd
from typing import Dict, Optional
from .base import BaseFactor


class FactorDebtRatio(BaseFactor):
    """负债率因子"""
    
    name = "DebtRatio"
    description = "负债率，衡量财务杠杆"
    direction = "lower"  # 越低越好
    weight = 0.15  # 默认权重 15%
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算负债率
        
        Args:
            stock_data: 包含 'liabilityToAsset' 列的 DataFrame
            
        Returns:
            负债率 Series
        """
        if 'liabilityToAsset' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'liabilityToAsset' 列")
        
        debt_ratio = stock_data['liabilityToAsset'].astype(float)
        
        # 处理无效值
        debt_ratio = debt_ratio.replace([float('inf'), float('-inf')], float('nan'))
        
        return debt_ratio
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'liabilityToAsset' in stock_data.columns and stock_data['liabilityToAsset'].notna().any()


class FactorDebtToEquity(BaseFactor):
    """负债权益比因子（D/E）"""
    
    name = "DebtToEquity"
    description = "负债权益比，衡量财务结构"
    direction = "lower"  # 越低越好
    weight = 0.15
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算负债权益比
        
        BaoStock 中 assetToEquity = 资产/权益
        所以 D/E = 1 / (assetToEquity - 1)
        
        Args:
            stock_data: 包含 'assetToEquity' 列的 DataFrame
            
        Returns:
            负债权益比 Series
        """
        if 'assetToEquity' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'assetToEquity' 列")
        
        asset_to_equity = stock_data['assetToEquity'].astype(float)
        
        # D/E = (资产-权益)/权益 = 资产/权益 - 1
        de_ratio = asset_to_equity - 1
        
        # 处理无效值和负值
        de_ratio = de_ratio.replace([float('inf'), float('-inf')], float('nan'))
        de_ratio = de_ratio.clip(lower=0.01)  # 至少0.01
        
        return de_ratio
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'assetToEquity' in stock_data.columns and stock_data['assetToEquity'].notna().any()


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("负债率因子测试")
    print("=" * 60)
    
    test_data = pd.DataFrame({
        'code': ['sh.600519', 'sh.600036', 'sh.600000'],
        'liabilityToAsset': [0.15, 0.92, 0.88]  # 茅台15%, 招行92%, 浦发88%
    }).set_index('code')
    
    factor = FactorDebtRatio()
    
    print("\n原始数据:")
    print(test_data)
    
    print("\n负债率:")
    print(factor.calculate(test_data))
    
    print("\n分数（越低越高分）:")
    print(factor.transform(factor.calculate(test_data)))
    
    print("\n" + "=" * 60)
