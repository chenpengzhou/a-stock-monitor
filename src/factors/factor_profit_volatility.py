# -*- coding: utf-8 -*-
"""
净利润波动率因子模块

净利润稳定性：衡量公司盈利的波动程度。

方向：越低越好
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import BaseFactor


class FactorProfitVolatility(BaseFactor):
    """净利润波动率因子"""
    
    name = "ProfitVolatility"
    description = "净利润波动率，衡量盈利稳定性"
    direction = "lower"  # 越低越好
    weight = 0.10  # 默认权重 10%
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化净利润波动率因子
        
        Args:
            config:
                quarters: 计算波动的季度数（默认8）
                method: 'cv'=变异系数, 'std'=标准差
        """
        super().__init__(config)
        
        self.quarters = self.config.get('quarters', 8)
        self.method = self.config.get('method', 'cv')
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算净利润波动率
        
        Args:
            stock_data: 包含 'netProfit' 和 'code' 列的 DataFrame
            
        Returns:
            波动率 Series
        """
        if 'netProfit' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'netProfit' 列")
        
        result = stock_data.groupby('code')['netProfit'].transform(
            lambda x: self._calc_volatility(x)
        )
        
        return result.astype(float)
    
    def _calc_volatility(self, series: pd.Series) -> float:
        """计算单只股票的净利润波动率"""
        recent = series.dropna().tail(self.quarters)
        
        if len(recent) < 2:
            return np.nan
        
        if self.method == 'cv':
            mean = recent.mean()
            if mean == 0:
                return np.nan
            return recent.std() / abs(mean)
        else:
            return recent.std()
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'netProfit' in stock_data.columns and stock_data['netProfit'].notna().any()


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("净利润波动率因子测试")
    print("=" * 60)
    
    np.random.seed(42)
    n_quarters = 8
    
    test_data = pd.DataFrame({
        'code': ['sh.600519'] * n_quarters + ['sh.600036'] * n_quarters,
        'report_date': [f'2024-Q{i}' for i in range(1, 5)] + [f'2023-Q{i}' for i in range(1, 5)],
        'netProfit': list(np.random.normal(50, 2, n_quarters)) +  # 稳定
                list(np.random.normal(50, 15, n_quarters))   # 不稳定
    })
    
    factor = FactorProfitVolatility()
    
    print("\n波动率:")
    vol = factor.calculate(test_data).drop_duplicates()
    print(vol)
    
    print("\n分数（越低越高分）:")
    scores = factor.transform(test_data.groupby('code')['netProfit'].first())
    print(scores)
    
    print("\n" + "=" * 60)
