# -*- coding: utf-8 -*-
"""
营收波动率因子模块

营收稳定性：衡量公司收入的波动程度。

方向：越低越好（稳定是防守型策略的核心）
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from .base import BaseFactor


class FactorRevenueVolatility(BaseFactor):
    """营收波动率因子"""
    
    name = "RevenueVolatility"
    description = "营收波动率，衡量收入稳定性"
    direction = "lower"  # 越低越好
    weight = 0.10  # 默认权重 10%
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化营收波动率因子
        
        Args:
            config:
                quarters: 计算波动的季度数（默认8）
                method: 'cv'=变异系数, 'std'=标准差
        """
        super().__init__(config)
        
        self.quarters = self.config.get('quarters', 8)
        self.method = self.config.get('method', 'cv')  # cv=变异系数
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算营收波动率
        
        Args:
            stock_data: 包含 'revenue' 和 'code' 列的 DataFrame
            
        Returns:
            波动率 Series
        """
        if 'revenue' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'revenue' 列")
        
        # 按股票分组计算波动率
        result = stock_data.groupby('code')['revenue'].transform(
            lambda x: self._calc_volatility(x)
        )
        
        return result.astype(float)
    
    def _calc_volatility(self, series: pd.Series) -> float:
        """
        计算单只股票的营收波动率
        """
        # 取最近 N 个季度
        recent = series.dropna().tail(self.quarters)
        
        if len(recent) < 2:
            return np.nan
        
        if self.method == 'cv':
            # 变异系数 = 标准差 / 均值
            mean = recent.mean()
            if mean == 0:
                return np.nan
            return recent.std() / abs(mean)
        else:
            # 标准差
            return recent.std()
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'revenue' in stock_data.columns and stock_data['revenue'].notna().any()


class FactorRevenueStability(BaseFactor):
    """营收稳定性因子（简化版：季度间变化率标准差）"""
    
    name = "RevenueStability"
    description = "营收季度变化率标准差"
    direction = "lower"
    weight = 0.10
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算营收季度变化率标准差
        """
        if 'revenue' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'revenue' 列")
        
        def calc_growth_std(group):
            revenue = group['revenue'].dropna()
            if len(revenue) < 2:
                return np.nan
            # 计算季度环比
            growth = revenue.pct_change()
            return growth.dropna().std()
        
        result = stock_data.groupby('code').apply(calc_growth_std)
        
        return result.astype(float)


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("营收波动率因子测试")
    print("=" * 60)
    
    # 模拟数据
    np.random.seed(42)
    n_quarters = 8
    
    test_data = pd.DataFrame({
        'code': ['sh.600519'] * n_quarters + ['sh.600036'] * n_quarters,
        'report_date': [f'2024-Q{i}' for i in range(1, 5)] + [f'2023-Q{i}' for i in range(1, 5)],
        'revenue': list(np.random.normal(100, 5, n_quarters)) +  # 稳定
                list(np.random.normal(100, 30, n_quarters))   # 不稳定
    })
    
    factor = FactorRevenueVolatility()
    
    print("\n测试数据（前几行）:")
    print(test_data.head())
    
    print("\n波动率:")
    vol = factor.calculate(test_data).drop_duplicates()
    print(vol)
    
    print("\n分数（越低越高分）:")
    scores = factor.transform(test_data.groupby('code')['revenue'].first())
    print(scores)
    
    print("\n" + "=" * 60)
