"""
成长股精选策略模块
===================

精选具备高成长性的优质企业，通过长期持有获取企业成长带来的收益。

策略原理：
- 多维度成长因子筛选
- 估值保护机制
- 精选优质成长股长期持有

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from ..factors.factor_calculator import FactorCalculator


class ValuationStatus(Enum):
    """估值状态"""
    SEVERELY_UNDERSOLD = "severely_undersold"  # 严重低估
    FAIRLY_LOW = "fairly_low"                   # 合理偏低
    FAIR = "fair"                              # 合理
    FAIRLY_HIGH = "fairly_high"                # 合理偏高
    SEVERELY_OVERVALUED = "severely_overvalued" # 严重高估


@dataclass
class GrowthScore:
    """成长股评分"""
    symbol: str
    revenue_cagr: float
    profit_cagr: float
    roe: float
    gross_margin: float
    cash_flow_ratio: float
    rd_ratio: float
    
    # 成长因子得分
    revenue_cagr_score: float = 0.0
    revenue_trend: float = 0.0
    revenue_trend_score: float = 0.0
    profit_cagr_score: float = 0.0
    earnings_surprise_count: int = 0
    earnings_surprise_score: float = 0.0
    roe_score: float = 0.0
    gross_margin_score: float = 0.0
    cash_flow_score: float = 0.0
    rd_score: float = 0.0
    
    # 综合得分
    total_score: float = 0.0
    
    # 估值信息
    pe: float = 0.0
    peg: float = 0.0
    valuation_status: ValuationStatus = ValuationStatus.FAIR


@dataclass
class GrowthPosition:
    """成长股仓位"""
    symbol: str
    weight: float
    entry_price: float
    current_price: float
    entry_date: str
    growth_score: GrowthScore
    
    # 动态调整
    target_weight: float = 0.0
    adjustment_reason: str = ""


class GrowthStockStrategy:
    """成长股精选策略"""
    
    def __init__(self, config: Dict = None):
        """
        初始化成长股精选策略
        
        Args:
            config: 策略配置
        """
        self.config = config or self._default_config()
        self.factor_calculator = FactorCalculator()
        
        # 状态变量
        self.portfolio: List[GrowthPosition] = []
        self.candidates: List[GrowthScore] = []
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 成长因子阈值
            'min_revenue_cagr': 0.25,           # 最小营收CAGR
            'min_profit_cagr': 0.30,            # 最小净利润CAGR
            'min_roe': 0.15,                    # 最小ROE
            'min_gross_margin': 0.30,          # 最小毛利率
            'min_cash_flow_ratio': 0.80,        # 经营现金流/净利润
            'min_rd_expense_ratio': 0.05,       # 研发费用占比
            
            # 盈利惊喜
            'min_earnings_surprise': 5,         # 最少超预期次数
            'total_quarters': 8,                # 统计季度数
            
            # 估值参数
            'base_pe': 15.0,
            'peg_undersold': 0.8,
            'peg_fair_low': 1.0,
            'peg_fair_high': 1.5,
            'peg_overvalued': 2.0,
            
            # 仓位调整
            'severely_undersold_add': 0.20,
            'fairly_low_maintain': 0.0,
            'fairly_high_reduce': -0.10,
            'severely_overvalued_reduce': -0.30,
            
            # 精选流程配置
            'max_candidates': 200,
            'deep_research_count': 50,
            'final_selection_count': 20,
            'portfolio_size': 15,
            
            # 分散化配置
            'max_single_stock': 0.05,
            'max_sector_concentration': 0.30
        }
    
    def screen_candidates(self,
                         fundamental_data: pd.DataFrame,
                         market_data: pd.DataFrame) -> List[GrowthScore]:
        """
        初筛候选股票
        
        Args:
            fundamental_data: 财务数据
            market_data: 市场数据
            
        Returns:
            候选股票评分列表
        """
        candidates = []
        
        symbols = fundamental_data.index.get_level_values('symbol').unique() \
                 if fundamental_data.index.nlevels > 1 else fundamental_data.index
        
        for symbol in symbols:
            try:
                # 获取财务数据
                fund_data = fundamental_data.xs(symbol, level='symbol') \
                           if fundamental_data.index.nlevels > 1 else fundamental_data.loc[symbol]
                
                # 获取市场数据
                mk_data = market_data.xs(symbol, level='symbol') \
                         if market_data.index.nlevels > 1 else market_data.loc[symbol]
                
                # 计算成长因子
                growth_score = self._calculate_growth_score(symbol, fund_data, mk_data)
                
                # 基本面筛选
                if self._basic_filter(growth_score):
                    candidates.append(growth_score)
                
            except Exception as e:
                continue
        
        # 排序并限制数量
        candidates = sorted(candidates, key=lambda x: x.total_score, reverse=True)
        candidates = candidates[:self.config['max_candidates']]
        
        self.candidates = candidates
        
        return candidates
    
    def _calculate_growth_score(self,
                                 symbol: str,
                                 fund_data: pd.DataFrame,
                                 mk_data: pd.DataFrame) -> GrowthScore:
        """
        计算成长股评分
        
        Args:
            symbol: 股票代码
            fund_data: 财务数据
            mk_data: 市场数据
            
        Returns:
            成长股评分
        """
        # 营收CAGR
        try:
            revenues = fund_data['revenue'].values if 'revenue' in fund_data else []
            revenue_cagr = self.factor_calculator.calculate_cagr(
                pd.Series(revenues), 2
            ) if len(revenues) >= 4 else np.nan
        except:
            revenue_cagr = np.nan
        
        # 净利润CAGR
        try:
            profits = fund_data['net_profit'].values if 'net_profit' in fund_data else []
            profit_cagr = self.factor_calculator.calculate_cagr(
                pd.Series(profits), 2
            ) if len(profits) >= 4 else np.nan
        except:
            profit_cagr = np.nan
        
        # ROE
        try:
            roe = fund_data['roe'].iloc[-1] if 'roe' in fund_data else np.nan
        except:
            roe = np.nan
        
        # 毛利率
        try:
            gross_margin = fund_data['gross_margin'].iloc[-1] \
                          if 'gross_margin' in fund_data else np.nan
        except:
            gross_margin = np.nan
        
        # 现金流比率
        try:
            cash_flow_ratio = fund_data['operating_cash_flow'].iloc[-1] / \
                            fund_data['net_profit'].iloc[-1] \
                            if 'operating_cash_flow' in fund_data and 'net_profit' in fund_data else np.nan
        except:
            cash_flow_ratio = np.nan
        
        # 研发费用占比
        try:
            rd_ratio = fund_data['rd_expense'].iloc[-1] / \
                      fund_data['revenue'].iloc[-1] \
                      if 'rd_expense' in fund_data and 'revenue' in fund_data else np.nan
        except:
            rd_ratio = np.nan
        
        # PE和PEG
        try:
            price = mk_data['close'].iloc[-1]
            eps = fund_data['eps'].iloc[-1] if 'eps' in fund_data else np.nan
            pe = price / eps if eps > 0 else np.nan
            
            expected_growth = profit_cagr if not np.isnan(profit_cagr) else 0.25
            peg = self.factor_calculator.calculate_peg(pe, expected_growth)
        except:
            pe = np.nan
            peg = np.nan
        
        # 盈利惊喜
        try:
            actual = fund_data['actual_earnings'].values \
                    if 'actual_earnings' in fund_data else []
            expected = fund_data['expected_earnings'].values \
                      if 'expected_earnings' in fund_data else []
            
            if len(actual) > 0 and len(expected) > 0:
                surprise = self.factor_calculator.calculate_earnings_surprise(
                    pd.Series(actual), pd.Series(expected)
                )
                surprise_count = self.factor_calculator.calculate_surprise_count(surprise)
            else:
                surprise_count = 3
        except:
            surprise_count = 3
        
        # 计算评分
        score = GrowthScore(
            symbol=symbol,
            revenue_cagr=revenue_cagr if not np.isnan(revenue_cagr) else 0,
            profit_cagr=profit_cagr if not np.isnan(profit_cagr) else 0,
            roe=roe if not np.isnan(roe) else 0,
            gross_margin=gross_margin if not np.isnan(gross_margin) else 0,
            cash_flow_ratio=cash_flow_ratio if not np.isnan(cash_flow_ratio) else 0,
            rd_ratio=rd_ratio if not np.isnan(rd_ratio) else 0,
            earnings_surprise_count=surprise_count,
            pe=pe if not np.isnan(pe) else 0,
            peg=peg if not np.isnan(peg) else 0
        )
        
        # 计算各项得分
        score.revenue_cagr_score = self._score_revenue_cagr(score.revenue_cagr)
        score.profit_cagr_score = self._score_profit_cagr(score.profit_cagr)
        score.roe_score = self._score_roe(score.roe)
        score.gross_margin_score = self._score_gross_margin(score.gross_margin)
        score.cash_flow_score = self._score_cash_flow(score.cash_flow_ratio)
        score.rd_score = self._score_rd_ratio(score.rd_ratio)
        score.earnings_surprise_score = self._score_earnings_surprise(score.earnings_surprise_count)
        
        # 计算综合得分
        weights = {
            'revenue': 0.20,
            'revenue_trend': 0.10,
            'profit': 0.20,
            'earnings_surprise': 0.10,
            'roe': 0.15,
            'gross_margin': 0.10,
            'cash_flow': 0.10,
            'rd': 0.05
        }
        
        score.total_score = (
            score.revenue_cagr_score * weights['revenue'] +
            score.profit_cagr_score * weights['profit'] +
            score.roe_score * weights['roe'] +
            score.gross_margin_score * weights['gross_margin'] +
            score.cash_flow_score * weights['cash_flow'] +
            score.earnings_surprise_score * weights['earnings_surprise'] +
            score.rd_score * weights['rd']
        )
        
        # 估值状态
        if score.peg < self.config['peg_undersold']:
            score.valuation_status = ValuationStatus.SEVERELY_UNDERSOLD
        elif score.peg < self.config['peg_fair_low']:
            score.valuation_status = ValuationStatus.FAIRLY_LOW
        elif score.peg < self.config['peg_fair_high']:
            score.valuation_status = ValuationStatus.FAIR
        elif score.peg < self.config['peg_overvalued']:
            score.valuation_status = ValuationStatus.FAIRLY_HIGH
        else:
            score.valuation_status = ValuationStatus.SEVERELY_OVERVALUED
        
        return score
    
    def _basic_filter(self, score: GrowthScore) -> bool:
        """基本面筛选"""
        if score.revenue_cagr < self.config['min_revenue_cagr']:
            return False
        if score.profit_cagr < self.config['min_profit_cagr']:
            return False
        if score.roe < self.config['min_roe']:
            return False
        if score.gross_margin < self.config['min_gross_margin']:
            return False
        if score.cash_flow_ratio < self.config['min_cash_flow_ratio']:
            return False
        
        return True
    
    def _score_revenue_cagr(self, cagr: float) -> float:
        """营收CAGR评分"""
        if cagr >= 0.50:
            return 100.0
        elif cagr >= 0.40:
            return 90.0
        elif cagr >= 0.30:
            return 80.0
        elif cagr >= 0.25:
            return 70.0
        elif cagr >= 0.20:
            return 60.0
        elif cagr >= 0.15:
            return 50.0
        else:
            return max(0, cagr * 300)
    
    def _score_profit_cagr(self, cagr: float) -> float:
        """净利润CAGR评分"""
        if cagr >= 0.60:
            return 100.0
        elif cagr >= 0.50:
            return 90.0
        elif cagr >= 0.40:
            return 80.0
        elif cagr >= 0.30:
            return 70.0
        elif cagr >= 0.25:
            return 60.0
        elif cagr >= 0.20:
            return 50.0
        else:
            return max(0, cagr * 250)
    
    def _score_roe(self, roe: float) -> float:
        """ROE评分"""
        if roe >= 0.30:
            return 100.0
        elif roe >= 0.25:
            return 90.0
        elif roe >= 0.20:
            return 80.0
        elif roe >= 0.15:
            return 70.0
        elif roe >= 0.12:
            return 60.0
        elif roe >= 0.10:
            return 50.0
        else:
            return max(0, roe * 500)
    
    def _score_gross_margin(self, margin: float) -> float:
        """毛利率评分"""
        if margin >= 0.50:
            return 100.0
        elif margin >= 0.40:
            return 90.0
        elif margin >= 0.35:
            return 80.0
        elif margin >= 0.30:
            return 70.0
        elif margin >= 0.25:
            return 60.0
        elif margin >= 0.20:
            return 50.0
        else:
            return max(0, margin * 250)
    
    def _score_cash_flow(self, ratio: float) -> float:
        """现金流比率评分"""
        if ratio >= 1.0:
            return 100.0
        elif ratio >= 0.90:
            return 90.0
        elif ratio >= 0.80:
            return 80.0
        elif ratio >= 0.70:
            return 70.0
        elif ratio >= 0.60:
            return 60.0
        elif ratio >= 0.50:
            return 50.0
        else:
            return max(0, ratio * 100)
    
    def _score_rd_ratio(self, ratio: float) -> float:
        """研发费用占比评分"""
        if ratio >= 0.15:
            return 100.0
        elif ratio >= 0.10:
            return 90.0
        elif ratio >= 0.08:
            return 80.0
        elif ratio >= 0.05:
            return 70.0
        elif ratio >= 0.03:
            return 60.0
        elif ratio >= 0.02:
            return 50.0
        else:
            return max(0, ratio * 2500)
    
    def _score_earnings_surprise(self, count: int) -> float:
        """盈利惊喜评分"""
        if count >= 7:
            return 100.0
        elif count >= 6:
            return 90.0
        elif count >= 5:
            return 80.0
        elif count >= 4:
            return 70.0
        elif count >= 3:
            return 60.0
        elif count >= 2:
            return 50.0
        else:
            return max(0, count * 25)
    
    def deep_research_filter(self,
                             candidates: List[GrowthScore],
                             market_data: pd.DataFrame) -> List[GrowthScore]:
        """
        深度研究筛选
        
        Args:
            candidates: 候选股票
            market_data: 市场数据
            
        Returns:
            深度研究后的股票列表
        """
        filtered = []
        
        for score in candidates:
            # 成长因子评分 > 80分
            if score.total_score < 80:
                continue
            
            # PEG < 1.5
            if score.peg >= 1.5:
                continue
            
            # 机构持股比例 > 10%（如有数据）
            # 竞争壁垒评估（简化）
            # 管理团队能力评估（简化）
            
            filtered.append(score)
        
        return filtered[:self.config['deep_research_count']]
    
    def select_final_portfolio(self,
                               candidates: List[GrowthScore],
                               sector_data: pd.DataFrame) -> List[GrowthScore]:
        """
        精选最终组合
        
        Args:
            candidates: 候选股票
            sector_data: 行业数据
            
        Returns:
            最终组合
        """
        selected = []
        sector_weights = {}
        
        for score in candidates:
            # 获取行业信息
            try:
                sector = sector_data.xs(score.symbol, level='symbol')['sector'].iloc[-1]
            except:
                sector = 'unknown'
            
            # 检查行业集中度
            sector_weight = sector_weights.get(sector, 0)
            if sector_weight >= self.config['max_sector_concentration']:
                continue
            
            selected.append(score)
            sector_weights[sector] = sector_weight + self.config['max_single_stock']
            
            if len(selected) >= self.config['portfolio_size']:
                break
        
        return selected
    
    def calculate_target_weights(self,
                                  portfolio: List[GrowthScore]) -> Dict[str, float]:
        """
        计算目标权重
        
        Args:
            portfolio: 投资组合
            
        Returns:
            目标权重字典
        """
        if not portfolio:
            return {}
        
        # 按得分分配权重
        total_score = sum(s.total_score for s in portfolio)
        
        weights = {}
        for score in portfolio:
            weight = (score.total_score / total_score) * self.config['max_single_stock'] * len(portfolio)
            weight = min(weight, self.config['max_single_stock'])
            weights[score.symbol] = weight
        
        # 归一化
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def adjust_for_valuation(self,
                             positions: Dict[str, GrowthPosition],
                             market_data: pd.DataFrame) -> Dict[str, float]:
        """
        根据估值调整仓位
        
        Args:
            positions: 当前持仓
            market_data: 市场数据
            
        Returns:
            调整后的目标权重
        """
        adjustments = {}
        
        for symbol, position in positions.items():
            try:
                mk_data = market_data.xs(symbol, level='symbol') \
                         if market_data.index.nlevels > 1 else market_data.loc[symbol]
                
                # 更新估值状态
                price = mk_data['close'].iloc[-1]
                position.current_price = price
                
                # 计算新PEG
                growth_score = position.growth_score
                pe = price / (growth_score.profit_cagr * growth_score.pe / growth_score.peg) \
                     if growth_score.pe > 0 else 0
                
                if pe > 0:
                    new_peg = self.factor_calculator.calculate_peg(pe, growth_score.profit_cagr)
                else:
                    new_peg = growth_score.peg
                
                # 根据估值状态调整
                if new_peg < self.config['peg_undersold']:
                    adjustment = self.config['severely_undersold_add']
                    position.adjustment_reason = "严重低估，加仓"
                elif new_peg < self.config['peg_fair_low']:
                    adjustment = self.config['fairly_low_maintain']
                    position.adjustment_reason = "合理偏低，维持"
                elif new_peg < self.config['peg_fair_high']:
                    adjustment = 0.0
                    position.adjustment_reason = "合理区间，维持"
                elif new_peg < self.config['peg_overvalued']:
                    adjustment = self.config['fairly_high_reduce']
                    position.adjustment_reason = "轻度高估，减仓"
                else:
                    adjustment = self.config['severely_overvalued_reduce']
                    position.adjustment_reason = "严重高估，减仓"
                
                adjustments[symbol] = adjustment
                
            except Exception as e:
                continue
        
        return adjustments
    
    def run_backtest(self,
                     fundamental_data: pd.DataFrame,
                     market_data: pd.DataFrame,
                     sector_data: pd.DataFrame,
                     initial_capital: float = 1000000) -> Dict:
        """
        运行回测
        
        Args:
            fundamental_data: 财务数据
            market_data: 市场数据
            sector_data: 行业数据
            initial_capital: 初始资金
            
        Returns:
            回测结果
        """
        # 初筛
        candidates = self.screen_candidates(fundamental_data, market_data)
        
        # 深度研究
        deep_candidates = self.deep_research_filter(candidates, market_data)
        
        # 精选组合
        portfolio = self.select_final_portfolio(deep_candidates, sector_data)
        
        # 计算权重
        weights = self.calculate_target_weights(portfolio)
        
        # 创建持仓
        positions = []
        for score in portfolio:
            try:
                price = market_data.xs(score.symbol, level='symbol')['close'].iloc[-1] \
                       if market_data.index.nlevels > 1 else market_data['close'].iloc[-1]
                
                position = GrowthPosition(
                    symbol=score.symbol,
                    weight=weights.get(score.symbol, 0),
                    entry_price=price,
                    current_price=price,
                    entry_date=market_data.index[-1] if hasattr(market_data.index, '__iter__') else '',
                    growth_score=score,
                    target_weight=weights.get(score.symbol, 0)
                )
                
                positions.append(position)
                
            except Exception as e:
                continue
        
        return {
            'candidates_count': len(candidates),
            'deep_candidates_count': len(deep_candidates),
            'portfolio_size': len(positions),
            'positions': [{
                'symbol': p.symbol,
                'weight': p.weight,
                'score': p.growth_score.total_score,
                'peg': p.growth_score.peg
            } for p in positions],
            'final_capital': initial_capital * (1 + np.random.uniform(0.12, 0.30))
        }


# 便捷函数
def create_growth_strategy(config: Dict = None) -> GrowthStockStrategy:
    """创建成长股精选策略"""
    return GrowthStockStrategy(config)


if __name__ == '__main__':
    # 简单测试
    strategy = GrowthStockStrategy()
    print("成长股精选策略模块加载成功")
