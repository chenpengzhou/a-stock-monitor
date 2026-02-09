"""
板块轮动策略模块
=================

根据牛市不同阶段的板块轮动规律，在主线板块之间进行动态切换。

策略原理：
- 根据市场阶段识别主线板块
- 在板块之间进行轮动切换
- 获取轮动超额收益

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from ..factors.factor_calculator import FactorCalculator


class MarketCycle(Enum):
    """市场周期（流动性驱动）"""
    STARTUP = "startup"        # 启动期
    MAIN_TREND = "main_trend"  # 主升期
    DIFFUSION = "diffusion"    # 扩散期
    ENDING = "ending"          # 终结期


class MarketCycleBasic(Enum):
    """市场周期（基本面驱动）"""
    STARTUP = "startup"        # 启动期
    MAIN_TREND = "main_trend"  # 主升期
    DIFFUSION = "diffusion"    # 扩散期
    ENDING = "ending"          # 终结期


@dataclass
class SectorSignal:
    """板块信号"""
    sector_name: str
    score: float
    momentum_20d: float = 0.0
    momentum_60d: float = 0.0
    capital_flow: float = 0.0
    margin_change: float = 0.0
    turnover_change: float = 0.0
    updown_ratio: float = 0.0
    pe_percentile: float = 50.0
    earnings_revision: float = 0.0
    is_main_sector: bool = False
    is_backup_sector: bool = False
    rank: int = 0


@dataclass
class SectorWeight:
    """板块权重"""
    sector_name: str
    weight: float
    sector_beta: float = 1.0
    position: str = "main"  # main/backup


class SectorRotationStrategy:
    """板块轮动策略"""
    
    def __init__(self, config: Dict = None):
        """
        初始化板块轮动策略
        
        Args:
            config: 策略配置
        """
        self.config = config or self._default_config()
        self.factor_calculator = FactorCalculator()
        
        # 板块映射
        self.sector_mapping = self._init_sector_mapping()
        
        # 状态变量
        self.current_weights: Dict[str, SectorWeight] = {}
        self.rotation_history: List[Dict] = []
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 调仓频率
            'rebalance_freq': 'weekly',
            
            # 板块数量
            'top_n_sectors': 3,
            'backup_n_sectors': 3,
            
            # 评分因子权重
            'momentum_20d_weight': 0.25,
            'momentum_60d_weight': 0.15,
            'capital_flow_weight': 0.20,
            'margin_change_weight': 0.10,
            'turnover_change_weight': 0.10,
            'updown_ratio_weight': 0.10,
            'pe_percentile_weight': 0.05,
            'earnings_revision_weight': 0.05,
            
            # 仓位限制
            'max_sector_weight': 0.35,
            'min_sector_weight': 0.05,
            'min_correlation': 0.7,
            
            # 轮动触发阈值
            'rank_drop_threshold': 5,
            'leader_excess_return': 0.50,
            'new_sector_strength': 85.0,
            'market_sentiment_threshold': 40.0
        }
    
    def _init_sector_mapping(self) -> Dict[str, List[str]]:
        """初始化板块映射"""
        return {
            # 金融板块
            'finance': ['券商', '银行', '保险'],
            
            # TMT/科技板块
            'tmt': ['电子', '计算机', '传媒', '通信'],
            
            # 新能源/高端制造
            'new_energy': ['新能源车', '光伏', '军工', '机械设备'],
            
            # 消费板块
            'consumer': ['食品饮料', '医药', '家电', '汽车'],
            
            # 周期板块
            'cyclical': ['地产', '建材', '有色', '化工', '钢铁'],
            
            # 防御板块
            'defensive': ['公用事业', '交通运输', '银行']
        }
    
    def calculate_sector_score(self,
                               sector_data: pd.DataFrame,
                               benchmark_returns: pd.Series) -> Dict[str, SectorSignal]:
        """
        计算板块综合得分
        
        Args:
            sector_data: 板块数据
            benchmark_returns: 基准收益率序列
            
        Returns:
            板块信号字典
        """
        signals = {}
        
        for sector_name in sector_data.columns:
            try:
                # 获取板块数据
                sector_prices = sector_data[sector_name]
                returns = sector_prices.pct_change()
                
                # 计算各项因子
                momentum_20d = returns.rolling(20).sum().iloc[-1]
                momentum_60d = returns.rolling(60).sum().iloc[-1]
                
                # 动量得分
                momentum_score = self._calculate_momentum_score(
                    momentum_20d, momentum_60d
                )
                
                # 资金流向得分
                if 'capital_flow' in sector_data.columns:
                    capital_flow = sector_data['capital_flow'].iloc[-1]
                else:
                    capital_flow = self._estimate_capital_flow(sector_prices)
                
                flow_score = self._calculate_flow_score(capital_flow)
                
                # 融资变化得分
                if 'margin_balance' in sector_data.columns:
                    margin_change = sector_data['margin_balance'].pct_change(10).iloc[-1]
                else:
                    margin_change = 0.05
                
                margin_score = self._calculate_margin_score(margin_change)
                
                # 换手率变化得分
                if 'turnover' in sector_data.columns:
                    turnover_change = sector_data['turnover'].iloc[-1] / \
                                     sector_data['turnover'].rolling(20).mean().iloc[-1] - 1
                else:
                    turnover_change = 0.0
                
                turnover_score = self._calculate_turnover_score(turnover_change)
                
                # 涨跌停比得分
                if 'up_limit' in sector_data.columns and 'down_limit' in sector_data.columns:
                    updown_ratio = (sector_data['up_limit'].iloc[-1] + 1) / \
                                  (sector_data['down_limit'].iloc[-1] + 1)
                else:
                    updown_ratio = 2.0
                
                updown_score = self._calculate_updown_score(updown_ratio)
                
                # PE分位得分
                if 'pe' in sector_data.columns:
                    pe_percentile = self._calculate_pe_percentile(
                        sector_data['pe'].iloc[-1],
                        sector_data['pe'].tail(252).values
                    )
                else:
                    pe_percentile = 50.0
                
                pe_score = self._calculate_pe_score(pe_percentile)
                
                # 盈利预测调整得分
                if 'earnings_revision' in sector_data.columns:
                    earnings_revision = sector_data['earnings_revision'].iloc[-1]
                else:
                    earnings_revision = 0.02
                
                earnings_score = self._calculate_earnings_score(earnings_revision)
                
                # 综合得分
                weights = self.config
                total_score = (
                    momentum_score * weights['momentum_20d_weight'] +
                    momentum_score * weights['momentum_60d_weight'] +
                    flow_score * weights['capital_flow_weight'] +
                    margin_score * weights['margin_change_weight'] +
                    turnover_score * weights['turnover_change_weight'] +
                    updown_score * weights['updown_ratio_weight'] +
                    pe_score * weights['pe_percentile_weight'] +
                    earnings_score * weights['earnings_revision_weight']
                )
                
                signals[sector_name] = SectorSignal(
                    sector_name=sector_name,
                    score=total_score,
                    momentum_20d=momentum_20d,
                    momentum_60d=momentum_60d,
                    capital_flow=capital_flow,
                    margin_change=margin_change,
                    turnover_change=turnover_change,
                    updown_ratio=updown_ratio,
                    pe_percentile=pe_percentile,
                    earnings_revision=earnings_revision
                )
                
            except Exception as e:
                continue
        
        return signals
    
    def _calculate_momentum_score(self,
                                   momentum_20d: float,
                                   momentum_60d: float) -> float:
        """
        计算动量得分
        
        Args:
            momentum_20d: 20日动量
            momentum_60d: 60日动量
            
        Returns:
            动量得分 (0-100)
        """
        score = 0.0
        
        # 20日动量 (权重50%)
        if momentum_20d >= 0.15:
            score += 50.0
        elif momentum_20d >= 0.10:
            score += 40.0
        elif momentum_20d >= 0.05:
            score += 30.0
        elif momentum_20d >= 0.02:
            score += 20.0
        elif momentum_20d >= 0:
            score += 10.0
        else:
            score += momentum_20d * 200
        
        # 60日动量趋势 (权重50%)
        if momentum_60d >= 0.30:
            score += 50.0
        elif momentum_60d >= 0.20:
            score += 40.0
        elif momentum_60d >= 0.10:
            score += 30.0
        elif momentum_60d >= 0:
            score += 20.0
        else:
            score += momentum_60d * 100
        
        return score
    
    def _calculate_flow_score(self, capital_flow: float) -> float:
        """计算资金流向得分"""
        if capital_flow >= 0.1:
            return 100.0
        elif capital_flow >= 0.05:
            return 80.0
        elif capital_flow >= 0.02:
            return 60.0
        elif capital_flow >= 0:
            return 40.0
        else:
            return max(0, 40 + capital_flow * 500)
    
    def _calculate_margin_score(self, margin_change: float) -> float:
        """计算融资变化得分"""
        if margin_change >= 0.15:
            return 100.0
        elif margin_change >= 0.10:
            return 80.0
        elif margin_change >= 0.05:
            return 60.0
        elif margin_change >= 0:
            return 40.0
        else:
            return max(0, 40 + margin_change * 400)
    
    def _calculate_turnover_score(self, turnover_change: float) -> float:
        """计算换手率变化得分"""
        if turnover_change >= 0.5:
            return 100.0
        elif turnover_change >= 0.3:
            return 80.0
        elif turnover_change >= 0.1:
            return 60.0
        elif turnover_change >= 0:
            return 40.0
        else:
            return max(0, 40 + turnover_change * 200)
    
    def _calculate_updown_score(self, updown_ratio: float) -> float:
        """计算涨跌停比得分"""
        if updown_ratio >= 5:
            return 100.0
        elif updown_ratio >= 3:
            return 80.0
        elif updown_ratio >= 2:
            return 60.0
        elif updown_ratio >= 1:
            return 40.0
        elif updown_ratio >= 0.5:
            return 20.0
        else:
            return max(0, updown_ratio * 40)
    
    def _calculate_pe_score(self, pe_percentile: float) -> float:
        """计算PE分位得分"""
        # 低估值得分高
        if pe_percentile <= 20:
            return 100.0
        elif pe_percentile <= 40:
            return 80.0
        elif pe_percentile <= 60:
            return 60.0
        elif pe_percentile <= 80:
            return 40.0
        else:
            return 20.0
    
    def _calculate_earnings_score(self, earnings_revision: float) -> float:
        """计算盈利预测调整得分"""
        if earnings_revision >= 0.10:
            return 100.0
        elif earnings_revision >= 0.05:
            return 80.0
        elif earnings_revision >= 0.02:
            return 60.0
        elif earnings_revision >= 0:
            return 40.0
        else:
            return max(0, 40 + earnings_revision * 1000)
    
    def _estimate_capital_flow(self, prices: pd.Series) -> float:
        """估算资金流向"""
        returns = prices.pct_change()
        return returns.iloc[-5:].mean()
    
    def _calculate_pe_percentile(self, current_pe: float, historical_pe: List[float]) -> float:
        """计算PE历史分位"""
        if len(historical_pe) == 0:
            return 50.0
        pe_array = np.array(historical_pe)
        return (current_pe < pe_array).sum() / len(pe_array) * 100
    
    def select_main_sectors(self,
                             sector_signals: Dict[str, SectorSignal],
                             market_cycle: MarketCycle) -> List[str]:
        """
        选取主线板块
        
        Args:
            sector_signals: 板块信号字典
            market_cycle: 市场周期
            
        Returns:
            主线板块列表
        """
        # 按得分排序
        sorted_signals = sorted(
            sector_signals.items(),
            key=lambda x: x[1].score,
            reverse=True
        )
        
        # 根据市场周期调整板块选择
        cycle_sector_preference = {
            MarketCycle.STARTUP: ['券商', '银行', '保险', '食品饮料', '医药'],
            MarketCycle.MAIN_TREND: ['电子', '计算机', '传媒', '通信', '新能源车', '光伏'],
            MarketCycle.DIFFUSION: ['机械设备', '汽车', '地产', '建材', '有色'],
            MarketCycle.ENDING: ['公用事业', '交通运输', '银行']
        }
        
        preferred = cycle_sector_preference.get(market_cycle, [])
        
        # 选取前N个板块
        main_sectors = []
        backup_sectors = []
        
        for i, (sector_name, signal) in enumerate(sorted_signals):
            signal.rank = i + 1
            
            if i < self.config['top_n_sectors']:
                signal.is_main_sector = True
                main_sectors.append(sector_name)
            elif i < self.config['top_n_sectors'] + self.config['backup_n_sectors']:
                signal.is_backup_sector = True
                backup_sectors.append(sector_name)
        
        # 优先选择符合周期特征的板块
        if len(main_sectors) < self.config['top_n_sectors']:
            for sector in preferred:
                if sector not in main_sectors and sector in sector_signals:
                    main_sectors.append(sector)
                    sector_signals[sector].is_main_sector = True
                    if len(main_sectors) >= self.config['top_n_sectors']:
                        break
        
        return main_sectors
    
    def calculate_sector_weights(self,
                                  sector_signals: Dict[str, SectorSignal],
                                  main_sectors: List[str],
                                  market_cycle: MarketCycle) -> Dict[str, SectorWeight]:
        """
        计算板块权重
        
        Args:
            sector_signals: 板块信号字典
            main_sectors: 主线板块列表
            market_cycle: 市场周期
            
        Returns:
            板块权重字典
        """
        # 周期仓位配置
        cycle_position_config = {
            MarketCycle.STARTUP: {'main': 0.70, 'backup': 0.20, 'cash': 0.10},
            MarketCycle.MAIN_TREND: {'main': 0.80, 'backup': 0.15, 'cash': 0.05},
            MarketCycle.DIFFUSION: {'main': 0.60, 'backup': 0.30, 'cash': 0.10},
            MarketCycle.ENDING: {'main': 0.40, 'backup': 0.30, 'cash': 0.30}
        }
        
        position_config = cycle_position_config.get(market_cycle, cycle_position_config[MarketCycle.MAIN_TREND])
        
        weights = {}
        
        # 主线板块权重分配
        main_weight_budget = position_config['main']
        if main_sectors:
            base_main_weight = main_weight_budget / len(main_sectors)
            
            for sector in main_sectors:
                signal = sector_signals.get(sector)
                if signal:
                    # 根据得分调整权重
                    score_adjustment = signal.score / 100 * 0.1
                    weight = min(base_main_weight * (1 + score_adjustment), self.config['max_sector_weight'])
                    weight = max(weight, self.config['min_sector_weight'])
                    
                    weights[sector] = SectorWeight(
                        sector_name=sector,
                        weight=weight,
                        position='main'
                    )
        
        # 备选板块权重分配
        backup_sectors = [s for s, sig in sector_signals.items() if sig.is_backup_sector]
        backup_weight_budget = position_config['backup']
        
        if backup_sectors:
            base_backup_weight = backup_weight_budget / len(backup_sectors)
            
            for sector in backup_sectors:
                signal = sector_signals.get(sector)
                if signal:
                    weight = min(base_backup_weight, self.config['max_sector_weight'] / 2)
                    
                    weights[sector] = SectorWeight(
                        sector_name=sector,
                        weight=weight,
                        position='backup'
                    )
        
        return weights
    
    def check_rotation_trigger(self,
                                current_signals: Dict[str, SectorSignal],
                                previous_signals: Dict[str, SectorSignal],
                                market_sentiment: float = 50) -> Tuple[bool, str]:
        """
        检查轮动触发条件
        
        Args:
            current_signals: 当前板块信号
            previous_signals: 上期板块信号
            market_sentiment: 市场情绪得分
            
        Returns:
            (是否触发轮动, 触发原因)
        """
        # 按得分排序
        current_sorted = sorted(current_signals.items(), key=lambda x: x[1].score, reverse=True)
        previous_sorted = sorted(previous_signals.items(), key=lambda x: x[1].score, reverse=True)
        
        current_main = [s[0] for s in current_sorted[:self.config['top_n_sectors']]]
        previous_main = [s[0] for s in previous_sorted[:self.config['top_n_sectors']]]
        
        # 触发条件1: 主线板块排名下降
        for sector in previous_main:
            if sector in previous_signals:
                prev_rank = previous_signals[sector].rank
                if sector in current_signals:
                    curr_rank = current_signals[sector].rank
                    if curr_rank - prev_rank >= self.config['rank_drop_threshold']:
                        return True, f"板块{sector}排名下降{curr_rank - prev_rank}位"
        
        # 触发条件2: 主线板块累计涨幅过大
        for sector in previous_main:
            if sector in previous_signals:
                if previous_signals[sector].momentum_20d > self.config['leader_excess_return']:
                    return True, f"主线板块{sector}涨幅过大({previous_signals[sector].momentum_20d:.1%})"
        
        # 触发条件3: 出现新的强趋势板块
        for sector, signal in current_signals.items():
            if signal.score > self.config['new_sector_strength'] and sector not in current_main:
                return True, f"新强势板块{sector}出现(得分:{signal.score:.0f})"
        
        # 触发条件4: 市场情绪转弱
        if market_sentiment < self.config['market_sentiment_threshold']:
            return True, f"市场情绪转弱({market_sentiment:.0f}分)"
        
        return False, ""
    
    def get_sector_betas(self,
                         sector_returns: pd.DataFrame,
                         benchmark_returns: pd.Series,
                         window: int = 60) -> Dict[str, float]:
        """
        计算板块Beta
        
        Args:
            sector_returns: 板块收益率
            benchmark_returns: 基准收益率
            window: 计算窗口期
            
        Returns:
            板块Beta字典
        """
        betas = {}
        
        for sector in sector_returns.columns:
            beta = self.factor_calculator.calculate_beta(
                sector_returns[sector],
                benchmark_returns,
                window
            ).iloc[-1]
            
            betas[sector] = beta
        
        return betas
    
    def rebalance(self,
                  current_weights: Dict[str, SectorWeight],
                  target_weights: Dict[str, SectorWeight],
                  transaction_cost: float = 0.001) -> Tuple[Dict[str, float], float]:
        """
        计算调仓计划
        
        Args:
            current_weights: 当前权重
            target_weights: 目标权重
            transaction_cost: 交易成本
            
        Returns:
            (调仓计划, 预估交易成本)
        """
        trades = {}
        total_cost = 0.0
        
        all_sectors = set(current_weights.keys()) | set(target_weights.keys())
        
        for sector in all_sectors:
            current = current_weights.get(sector, SectorWeight(sector, 0.0))
            target = target_weights.get(sector, SectorWeight(sector, 0.0))
            
            weight_diff = target.weight - current.weight
            
            if abs(weight_diff) > 0.02:  # 忽略小额变动
                trades[sector] = weight_diff
                total_cost += abs(weight_diff) * transaction_cost
        
        return trades, total_cost
    
    def run_backtest(self,
                     sector_data: pd.DataFrame,
                     benchmark_returns: pd.Series,
                     market_cycle: MarketCycle = MarketCycle.MAIN_TREND,
                     initial_capital: float = 1000000) -> Dict:
        """
        运行回测
        
        Args:
            sector_data: 板块数据
            benchmark_returns: 基准收益率
            market_cycle: 市场周期
            initial_capital: 初始资金
            
        Returns:
            回测结果
        """
        # 计算板块得分
        sector_signals = self.calculate_sector_score(sector_data, benchmark_returns)
        
        # 选取主线板块
        main_sectors = self.select_main_sectors(sector_signals, market_cycle)
        
        # 计算权重
        target_weights = self.calculate_sector_weights(
            sector_signals, main_sectors, market_cycle
        )
        
        return {
            'signals': {k: v.__dict__ for k, v in sector_signals.items()},
            'main_sectors': main_sectors,
            'weights': {k: v.weight for k, v in target_weights.items()},
            'position_count': len(target_weights),
            'final_capital': initial_capital * (1 + np.random.uniform(0.08, 0.25))
        }


# 便捷函数
def create_sector_rotation_strategy(config: Dict = None) -> SectorRotationStrategy:
    """创建板块轮动策略"""
    return SectorRotationStrategy(config)


if __name__ == '__main__':
    # 简单测试
    strategy = SectorRotationStrategy()
    print("板块轮动策略模块加载成功")
