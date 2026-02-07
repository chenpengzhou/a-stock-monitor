# -*- coding: utf-8 -*-
"""
ROE 因子模块

净资产收益率（Return on Equity）
衡量公司使用股东资本的效率。

方向：越高越好
"""

import pandas as pd
from typing import Dict, Optional
from .base import BaseFactor


class FactorROE(BaseFactor):
    """ROE 因子"""
    
    name = "ROE"
    description = "净资产收益率，衡量股东资本回报效率"
    direction = "higher"
    weight = 0.15  # 默认权重 15%
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 ROE 因子
        
        Args:
            config:
                source: 数据来源 ('roeAvg' 或 'dupontROE')
                use_dupont: 是否使用杜邦分析的ROE（默认False，使用盈利能力表的roeAvg）
        """
        super().__init__(config)
        
        self.source = self.config.get('source', 'roeAvg')
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算 ROE
        
        Args:
            stock_data: 包含 'roe' 列的 DataFrame
            
        Returns:
            ROE 值 Series
        """
        # 支持多种列名映射
        if 'roe' in stock_data.columns:
            roe = stock_data['roe'].astype(float)
        elif self.source == 'dupontROE' and 'dupontROE' in stock_data.columns:
            roe = stock_data['dupontROE'].astype(float)
        elif 'roeAvg' in stock_data.columns:
            roe = stock_data['roeAvg'].astype(float)
        else:
            raise KeyError("stock_data 必须包含 'roe', 'roeAvg' 或 'dupontROE' 列")
        
        # 处理无效值
        roe = roe.replace([float('inf'), float('-inf')], float('nan'))
        
        return roe
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """
        验证 ROE 数据是否可用
        """
        has_roe = (
            'roe' in stock_data.columns or
            'roeAvg' in stock_data.columns or
            'dupontROE' in stock_data.columns
        )
        
        # ROE 不能全为空
        if has_roe:
            if 'roe' in stock_data.columns:
                return stock_data['roe'].notna().any()
            elif 'roeAvg' in stock_data.columns:
                return stock_data['roeAvg'].notna().any()
        
        return False


class FactorROETTM(BaseFactor):
    """ROE TTM 因子（过去12个月累计）"""
    
    name = "ROE_TTM"
    description = "过去12个月累计 ROE"
    direction = "higher"
    weight = 0.15
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算 ROE TTM
        
        Args:
            stock_data: 包含 'roe' 和 'report_date' 列的 DataFrame
            
        Returns:
            ROE TTM Series
        """
        # 按股票分组，计算滚动平均
        if 'roe' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'roe' 列")
        
        result = stock_data.groupby('code')['roe'].transform(
            lambda x: x.head(4).mean()  # 取最近4个季度
        )
        
        return result.astype(float)


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("ROE 因子测试")
    print("=" * 60)
    
    # 测试数据
    test_data = pd.DataFrame({
        'code': ['sh.600519', 'sh.600036', 'sh.600000'],
        'roe': [0.28, 0.12, 0.08],  # 28%, 12%, 8%
        'roeAvg': [0.28, 0.12, 0.08]
    }).set_index('code')
    
    factor = FactorROE()
    
    print("\n原始数据:")
    print(test_data)
    
    print("\nROE 值:")
    roe_values = factor.calculate(test_data)
    print(roe_values)
    
    print("\n转换分数（1-10分）:")
    scores = factor.transform(roe_values)
    print(scores)
    
    print("\n" + "=" * 60)
