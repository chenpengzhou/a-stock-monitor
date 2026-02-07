# -*- coding: utf-8 -*-
"""
净利润趋势因子模块

净利润变化趋势：结合 YoY 和 QoQ 变化。

- YoY（同比）：消除季节性，看年度增长
- QoQ（环比）：看近期边际变化

根据行业配置不同权重：
- 消费/地产：YoY 70%, QoQ 30%
- 医药/金融/公用：YoY 60%, QoQ 40%
- 科技：YoY 50%, QoQ 50%

方向：越高越好
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import BaseFactor


class FactorProfitTrend(BaseFactor):
    """净利润趋势因子"""
    
    name = "ProfitTrend"
    description = "净利润趋势（YoY+QqQ加权），衡量盈利变化方向"
    direction = "higher"
    weight = 0.15  # 默认权重 15%
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化净利润趋势因子
        
        Args:
            config:
                yoy_weight: 默认YoY权重
                qoq_weight: 默认QoQ权重
                use_industry_weights: 是否使用行业差异化权重（默认True）
        """
        super().__init__(config)
        
        self.yoy_weight = self.config.get('yoy_weight', 0.60)
        self.qoq_weight = self.config.get('qoq_weight', 0.40)
        self.use_industry = self.config.get('use_industry_weights', True)
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """
        计算净利润趋势得分
        
        Args:
            stock_data: 包含 'netProfit', 'code', 'industry', 'report_date' 列
            
        Returns:
            趋势得分 Series（已经是加权分数）
        """
        if 'netProfit' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'netProfit' 列")
        
        # 计算 YoY 和 QoQ 变化率
        yoy = self._calc_yoy(stock_data)
        qoq = self._calc_qoq(stock_data)
        
        # 获取权重
        if self.use_industry and 'industry' in stock_data.columns:
            weights = stock_data.groupby('code')['industry'].first().apply(
                lambda x: self._get_weights(x)
            )
        else:
            weights = pd.Series({
                code: (self.yoy_weight, self.qoq_weight) 
                for code in stock_data['code'].unique()
            })
        
        # 计算加权得分
        result = pd.Series(index=stock_data['code'].unique(), dtype=float)
        
        for code in result.index:
            yoy_val = yoy.get(code, 0)
            qoq_val = qoq.get(code, 0)
            yoy_w, qoq_w = weights.get(code, (self.yoy_weight, self.qoq_weight))
            
            # 标准化到 0-1
            yoy_norm = self._normalize_change(yoy_val)
            qoq_norm = self._normalize_change(qoq_val)
            
            # 加权
            result[code] = yoy_norm * yoy_w + qoq_norm * qoq_w
        
        return result
    
    def _get_weights(self, industry: str) -> tuple:
        """根据行业获取 YoY/QoQ 权重"""
        if not industry:
            return (self.yoy_weight, self.qoq_weight)
        
        try:
            from ..utils import get_weights_from_name
            return get_weights_from_name(industry)
        except ImportError:
            return (self.yoy_weight, self.qoq_weight)
    
    def _calc_yoy(self, stock_data: pd.DataFrame) -> dict:
        """计算 YoY 变化率"""
        yoy = {}
        
        for code, group in stock_data.groupby('code'):
            profit = group.sort_values('report_date')['netProfit'].dropna()
            
            if len(profit) < 2:
                yoy[code] = 0
                continue
            
            # 最新季度 vs 去年同期
            latest = profit.iloc[-1]
            last_year = profit.iloc[-5] if len(profit) >= 5 else profit.iloc[0]
            
            if last_year == 0 or pd.isna(last_year):
                yoy[code] = 0
            else:
                yoy[code] = (latest - last_year) / abs(last_year)
        
        return yoy
    
    def _calc_qoq(self, stock_data: pd.DataFrame) -> dict:
        """计算 QoQ 变化率"""
        qoq = {}
        
        for code, group in stock_data.groupby('code'):
            profit = group.sort_values('report_date')['netProfit'].dropna()
            
            if len(profit) < 2:
                qoq[code] = 0
                continue
            
            # 最新季度 vs 上季度
            latest = profit.iloc[-1]
            previous = profit.iloc[-2]
            
            if previous == 0 or pd.isna(previous):
                qoq[code] = 0
            else:
                qoq[code] = (latest - previous) / abs(previous)
        
        return qoq
    
    def _normalize_change(self, change: float) -> float:
        """
        标准化变化率为 0-1
        - 扭亏为盈（负→正）= 1.0
        - 大幅增长（>50%）= 0.9
        - 温和增长（0-50%）= 0.5-0.7
        - 下降 = <0.5
        """
        if pd.isna(change) or np.isinf(change):
            return 0.5
        
        if change > 1:  # 翻倍以上
            return 1.0
        elif change > 0.5:  # 50%-100%
            return 0.9
        elif change > 0.2:  # 20%-50%
            return 0.7
        elif change > 0:  # 0-20%
            return 0.5
        elif change > -0.2:  # -20%-0%
            return 0.3
        elif change > -0.5:  # -50%--20%
            return 0.1
        else:  # 下降超50%
            return 0.0
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据"""
        return 'netProfit' in stock_data.columns and stock_data['netProfit'].notna().any()


class FactorYoY(BaseFactor):
    """净利润 YoY 变化因子（单独使用）"""
    
    name = "YoYProfit"
    description = "净利润同比变化率"
    direction = "higher"
    weight = 0.15
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """计算 YoY"""
        if 'netProfit' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'netProfit' 列")
        
        yoy = {}
        for code, group in stock_data.groupby('code'):
            profit = group.sort_values('report_date')['netProfit'].dropna()
            
            if len(profit) < 5:
                yoy[code] = 0
            else:
                latest = profit.iloc[-1]
                last_year = profit.iloc[-5]
                
                if last_year == 0 or pd.isna(last_year):
                    yoy[code] = 0
                else:
                    yoy[code] = (latest - last_year) / abs(last_year)
        
        return pd.Series(yoy)


class FactorQoQ(BaseFactor):
    """净利润 QoQ 变化因子（单独使用）"""
    
    name = "QoQProfit"
    description = "净利润环比变化率"
    direction = "higher"
    weight = 0.10
    
    def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        """计算 QoQ"""
        if 'netProfit' not in stock_data.columns:
            raise KeyError("stock_data 必须包含 'netProfit' 列")
        
        qoq = {}
        for code, group in stock_data.groupby('code'):
            profit = group.sort_values('report_date')['netProfit'].dropna()
            
            if len(profit) < 2:
                qoq[code] = 0
            else:
                latest = profit.iloc[-1]
                previous = profit.iloc[-2]
                
                if previous == 0 or pd.isna(previous):
                    qoq[code] = 0
                else:
                    qoq[code] = (latest - previous) / abs(previous)
        
        return pd.Series(qoq)


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("净利润趋势因子测试")
    print("=" * 60)
    
    # 模拟数据
    np.random.seed(42)
    
    test_data = pd.DataFrame({
        'code': ['sh.600519'] * 8 + ['sh.600036'] * 8,
        'report_date': ['2023-Q' + str(i) for i in range(1, 5)] * 2 +
                       ['2024-Q' + str(i) for i in range(1, 5)] * 2,
        'industry': ['C15酒、饮料和精制茶制造业'] * 8 + ['J66货币金融服务'] * 8,
        'netProfit': (
            list(np.random.normal(50, 5, 4)) +  # 2023年
            list(np.random.normal(60, 5, 4)) +  # 2024年 增长
            list(np.random.normal(100, 10, 4)) +  # 2023年
            list(np.random.normal(90, 10, 4))   # 2024年 下降
        )
    })
    
    factor = FactorProfitTrend()
    
    print("\n测试数据:")
    print(test_data)
    
    print("\n趋势得分:")
    scores = factor.calculate(test_data)
    print(scores)
    
    print("\n" + "=" * 60)
