#!/usr/bin/env python3
"""
低波策略因子计算模块

核心因子:
- 波动率因子 (40%)
- ATR因子 (25%)
- Beta因子 (20%)
- 质量因子 (15%)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class VolatilityFactor:
    """波动率因子"""
    
    def __init__(self, window: int = 20):
        self.name = "volatility"
        self.window = window
        self.weight = 0.40
    
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """计算20日波动率"""
        returns = df['close'].pct_change()
        volatility = returns.rolling(self.window).std() * np.sqrt(252)
        return volatility
    
    def rank(self, df: pd.DataFrame) -> pd.Series:
        """波动率排名（越低越好）"""
        vol = self.calculate(df)
        return vol.rank(ascending=True)


class ATRFactor:
    """ATR因子"""
    
    def __init__(self, window: int = 14):
        self.name = "atr"
        self.window = window
        self.weight = 0.25
    
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """计算ATR"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.window).mean()
        return atr
    
    def filter(self, df: pd.DataFrame) -> pd.Series:
        """ATR过滤：ATR < 5日均值"""
        atr = self.calculate(df)
        atr_ma5 = atr.rolling(5).mean()
        return atr < atr_ma5


class BetaFactor:
    """Beta因子"""
    
    def __init__(self, window: int = 60):
        self.name = "beta"
        self.window = window
        self.weight = 0.20
    
    def calculate(self, df: pd.DataFrame, market_returns: pd.Series = None) -> pd.Series:
        """计算Beta（相对于市场）"""
        if market_returns is None:
            # 假设市场收益
            market_returns = df['close'].pct_change()
        
        stock_returns = df['close'].pct_change()
        
        # 计算滚动Beta
        covariance = stock_returns.rolling(self.window).cov(market_returns)
        market_variance = market_returns.rolling(self.window).var()
        
        beta = covariance / market_variance
        return beta
    
    def rank(self, df: pd.DataFrame, market_returns: pd.Series = None) -> pd.Series:
        """Beta排名（越低越好）"""
        beta = self.calculate(df, market_returns)
        return beta.rank(ascending=True)


class QualityFactor:
    """质量因子 (ROE)"""
    
    def __init__(self, min_roe: float = 10.0):
        self.name = "quality"
        self.weight = 0.15
        self.min_roe = min_roe
    
    def filter(self, df: pd.DataFrame) -> pd.Series:
        """ROE过滤：ROE > 10%"""
        if 'roe' in df.columns:
            return df['roe'] > self.min_roe
        return pd.Series(True, index=df.index)
    
    def rank(self, df: pd.DataFrame) -> pd.Series:
        """质量排名（越高越好）"""
        if 'roe' in df.columns:
            return df['roe'].rank(ascending=False)
        return pd.Series(0, index=df.index)


class LowVolFactor:
    """低波策略综合因子"""
    
    def __init__(self):
        self.vol_factor = VolatilityFactor()
        self.atr_factor = ATRFactor()
        self.beta_factor = BetaFactor()
        self.quality_factor = QualityFactor()
    
    def calculate_score(self, df: pd.DataFrame, market_returns: pd.Series = None) -> pd.Series:
        """计算综合得分"""
        # 标准化各因子
        vol_score = self.vol_factor.rank(df)
        beta_score = self.beta_factor.rank(df, market_returns)
        quality_score = self.quality_factor.rank(df)
        
        # 归一化
        vol_norm = (vol_score - vol_score.min()) / (vol_score.max() - vol_score.min() + 1e-8)
        beta_norm = (beta_score - beta_score.min()) / (beta_score.max() - beta_score.min() + 1e-8)
        quality_norm = (quality_score - quality_score.min()) / (quality_score.max() - quality_score.min() + 1e-8)
        
        # 综合得分（波动率和Beta越低越好，所以用 1 - normalized）
        combined = (
            (1 - vol_norm) * self.vol_factor.weight +
            (1 - beta_norm) * self.beta_factor.weight +
            quality_norm * self.quality_factor.weight
        )
        
        return combined
    
    def select_stocks(self, df: pd.DataFrame, market_returns: pd.Series = None, 
                     top_n: int = 30, market_type: str = 'bear') -> list:
        """
        选股
        
        Args:
            df: 股票数据
            market_returns: 市场收益
            top_n: 选择数量
            market_type: 市场类型 (bull/bear/neutral)
        
        Returns:
            选中的股票代码列表
        """
        # 1. ATR过滤
        atr_filter = self.atr_factor.filter(df)
        
        # 2. 质量过滤
        quality_filter = self.quality_factor.filter(df)
        
        # 3. 计算综合得分
        scores = self.calculate_score(df, market_returns)
        
        # 4. 应用过滤
        scores = scores[atr_filter & quality_filter]
        
        # 5. 根据市场类型调整选股数量
        if market_type == 'bear':
            n = top_n
        elif market_type == 'neutral':
            n = int(top_n * 0.5)
        else:  # bull
            n = 0  # 牛市不选
        
        # 6. 选择得分最高的
        if n > 0:
            selected = scores.nlargest(n).index.tolist()
        else:
            selected = []
        
        return selected


if __name__ == "__main__":
    print("LowVol Factor Module loaded")
    factor = LowVolFactor()
    print(f"Factors: {factor.vol_factor.name}, {factor.atr_factor.name}, {factor.beta_factor.name}, {factor.quality_factor.name}")
