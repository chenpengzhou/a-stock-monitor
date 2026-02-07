# -*- coding: utf-8 -*-
"""
净利润率因子模块

净利润率（Net Profit Margin）
衡量公司净利润占营收的比例。

方向：越高越好
"""

import pandas as pd
from typing import Dict, Optional
from .base import BaseFactor


class FactorProfitMargin(BaseFactor):
    """净利润率因子"""
    
    name = "ProfitMargin"
    description = "净利润率，衡量盈利能力"
    direction = "higher"
    weight = 0.10  # 默认权重 10%
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算净利润率
        
        Args:
            stock_data: 包含 'npMargin' 列的 DataFrame
            
        Returns:
            净利润率 Series
        """
        if 'npMargin' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'npMargin' 列")
        
        margin = stock_data['npMargin'].astype(float)
        
        # 处理无效值
        margin = margin.replace([float('inf'), float('-inf')], float('nan'))
        
        return margin
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'npMargin' in stock_data.columns and stock_data['npMargin'].notna().any()


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("净利润率因子测试")
    print("=" * 60)
    
    test_data = pd.DataFrame({
        'code': ['sh.600519', 'sh.600036', 'sh.600000'],
        'npMargin': [0.52, 0.35, 0.28]  # 52%, 35%, 28%
    }).set_index('code')
    
    factor = FactorProfitMargin()
    
    print("\n原始数据:")
    print(test_data)
    
    print("\n净利润率:")
    print(factor.calculate(test_data))
    
    print("\n分数:")
    print(factor.transform(factor.calculate(test_data)))
    
    print("\n" + "=" * 60)
