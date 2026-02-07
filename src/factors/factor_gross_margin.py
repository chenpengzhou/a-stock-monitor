# -*- coding: utf-8 -*-
"""
毛利率因子模块

毛利率（Gross Margin）
衡量公司的定价能力和成本控制。

方向：越高越好
"""

import pandas as pd
from typing import Dict, Optional
from .base import BaseFactor


class FactorGrossMargin(BaseFactor):
    """毛利率因子"""
    
    name = "GrossMargin"
    description = "毛利率，衡量定价能力和成本控制"
    direction = "higher"
    weight = 0.10  # 默认权重 10%
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算毛利率
        
        Args:
            stock_data: 包含 'gpMargin' 列的 DataFrame
            
        Returns:
            毛利率 Series
        """
        if 'gpMargin' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'gpMargin' 列")
        
        margin = stock_data['gpMargin'].astype(float)
        
        # 处理无效值
        margin = margin.replace([float('inf'), float('-inf')], float('nan'))
        
        return margin
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'gpMargin' in stock_data.columns and stock_data['gpMargin'].notna().any()


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("毛利率因子测试")
    print("=" * 60)
    
    test_data = pd.DataFrame({
        'code': ['sh.600519', 'sh.600036', 'sh.600000'],
        'gpMargin': [0.92, 0.45, 0.28]  # 茅台92%, 银行45%, 某银行28%
    }).set_index('code')
    
    factor = FactorGrossMargin()
    
    print("\n原始数据:")
    print(test_data)
    
    print("\n毛利率:")
    print(factor.calculate(test_data))
    
    print("\n分数:")
    print(factor.transform(factor.calculate(test_data)))
    
    print("\n" + "=" * 60)
