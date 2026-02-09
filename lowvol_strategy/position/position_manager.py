"""
仓位管理模块
============

本模块提供低波动率策略的仓位管理功能。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.lowvol_config import LowVolConfig


class PositionManager:
    """
    仓位管理器
    """
    
    def __init__(self, config: LowVolConfig = None):
        self.config = config or LowVolConfig()
    
    def calculate_equal_weight(
        self,
        stock_list: List[str],
        capital: float = None
    ) -> Dict[str, float]:
        n = len(stock_list)
        if n == 0:
            return {}
        
        weight_per_stock = 1.0 / n
        weights = {stock: weight_per_stock for stock in stock_list}
        return weights
    
    def calculate_inverse_volatility_weight(
        self,
        stock_volatility: Dict[str, float],
        capital: float = None
    ) -> Dict[str, float]:
        if not stock_volatility:
            return {}
        
        inv_vol = {stock: 1.0 / (vol + 1e-8) for stock, vol in stock_volatility.items()}
        total = sum(inv_vol.values())
        weights = {stock: w / total for stock, w in inv_vol.items()}
        return weights
    
    def apply_single_stock_limit(
        self,
        weights: Dict[str, float],
        max_weight: float = None
    ) -> Dict[str, float]:
        if max_weight is None:
            max_weight = self.config.MAX_SINGLE_WEIGHT
        
        adjusted = weights.copy()
        
        for stock, weight in adjusted.items():
            if weight > max_weight:
                adjusted[stock] = max_weight
        
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {stock: w / total for stock, w in adjusted.items()}
        
        return adjusted
    
    def apply_industry_limit(
        self,
        weights: Dict[str, float],
        stock_industry: Dict[str, str],
        max_industry_weight: float = None
    ) -> Dict[str, float]:
        if max_industry_weight is None:
            max_industry_weight = self.config.MAX_INDUSTRY_WEIGHT
        
        adjusted = weights.copy()
        
        industry_weights = {}
        for stock, weight in adjusted.items():
            industry = stock_industry.get(stock, 'Unknown')
            if industry not in industry_weights:
                industry_weights[industry] = 0
            industry_weights[industry] += weight
        
        for industry, total_weight in industry_weights.items():
            if total_weight > max_industry_weight:
                excess_ratio = (total_weight - max_industry_weight) / total_weight
                
                for stock, weight in adjusted.items():
                    if stock_industry.get(stock) == industry:
                        excess_weight = weight * excess_ratio
                        adjusted[stock] -= excess_weight
        
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {stock: w / total for stock, w in adjusted.items()}
        
        return adjusted
    
    def apply_risk_controls(
        self,
        weights: Dict[str, float],
        stock_industry: Dict[str, str] = None,
        max_stock_weight: float = None,
        max_industry_weight: float = None
    ) -> Dict[str, float]:
        adjusted = self.apply_single_stock_limit(weights, max_stock_weight)
        
        if stock_industry:
            adjusted = self.apply_industry_limit(adjusted, stock_industry, max_industry_weight)
        
        return adjusted
    
    def calculate_position_sizes(
        self,
        weights: Dict[str, float],
        capital: float = None,
        prices: Dict[str, float] = None
    ) -> Dict[str, float]:
        if capital is None:
            capital = self.config.INITIAL_CAPITAL
        
        if not weights:
            return {}
        
        if prices:
            position_sizes = {}
            for stock, weight in weights.items():
                if stock in prices:
                    stock_capital = capital * weight
                    shares = int(stock_capital / prices[stock])
                    position_sizes[stock] = shares
                else:
                    position_sizes[stock] = 0
        else:
            position_sizes = {stock: weight for stock, weight in weights.items()}
        
        return position_sizes
    
    def check_stop_loss(
        self,
        positions: Dict[str, float],
        current_prices: Dict[str, float],
        cost_basis: Dict[str, float],
        threshold: float = None
    ) -> List[str]:
        if threshold is None:
            threshold = self.config.STOP_LOSS_THRESHOLD
        
        stocks_to_stop = []
        
        for stock, shares in positions.items():
            if shares <= 0:
                continue
            
            if stock not in current_prices or stock not in cost_basis:
                continue
            
            current_price = current_prices[stock]
            cost_price = cost_basis[stock]
            
            return_pct = (current_price - cost_price) / cost_price * 100
            
            if return_pct <= threshold:
                stocks_to_stop.append(stock)
        
        return stocks_to_stop
    
    def rebalance(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        turnover_threshold: float = 0.05
    ) -> Dict[str, float]:
        adjusted = target_weights.copy()
        
        for stock, target in target_weights.items():
            current = current_weights.get(stock, 0)
            diff = abs(target - current)
            
            if diff < turnover_threshold:
                adjusted[stock] = current
        
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {stock: w / total for stock, w in adjusted.items()}
        
        return adjusted
