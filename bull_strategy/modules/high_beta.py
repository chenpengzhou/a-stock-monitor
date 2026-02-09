"""
高Beta策略模块
===============

进攻核心策略，通过集中配置高弹性资产获取牛市超额收益。

策略原理：
- Beta值越高，随市场上涨的幅度越大
- 在牛市主升期使用高Beta策略获取最大收益
- 根据市场阶段动态调整仓位和杠杆

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from ..factors.factor_calculator import FactorCalculator


@dataclass
class HighBetaSignal:
    """高Beta选股信号"""
    symbol: str
    beta: float
    volatility: float
    daily_turnover: float
    market_cap: float
    return_60d: float
    roe: float
    score: float = 0.0
    is_selected: bool = False


@dataclass
class HighBetaPosition:
    """高Beta策略仓位"""
    symbol: str
    weight: float
    beta_target: float
    current_beta: float


class HighBetaStrategy:
    """高Beta策略"""
    
    def __init__(self, config=None):
        """
        初始化高Beta策略
        
        Args:
            config: 策略配置
        """
        self.config = config or self._default_config()
        self.factor_calculator = FactorCalculator()
        
        # 状态变量
        self.positions: Dict[str, HighBetaPosition] = {}
        self.historical_signals: List[Dict] = []
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'beta_threshold': 1.5,           # Beta阈值
            'min_daily_turnover': 5.0,       # 最小日均成交额(亿元)
            'min_market_cap': 100.0,         # 最小流通市值(亿元)
            'max_market_cap': 2000.0,         # 最大流通市值(亿元)
            'min_return_60d': 0.15,           # 60日最小涨幅
            'min_roe': 0.10,                 # 最小ROE
            'volatility_low': 0.30,          # 波动率下限
            'volatility_high': 0.80,          # 波动率上限
            'max_single_position': 0.05,      # 单股最大仓位
            'max_sector_position': 0.35,     # 单板块最大仓位
            'rebalance_freq': 'monthly'      # 调仓频率
        }
    
    def select_stocks(self,
                      market_data: pd.DataFrame,
                      benchmark_returns: pd.Series,
                      market_stage: str = 'main_trend') -> List[HighBetaSignal]:
        """
        高Beta选股
        
        Args:
            market_data: 市场数据 (包含close, volume, market_cap等)
            benchmark_returns: 基准收益率序列
            market_stage: 市场阶段
            
        Returns:
            高Beta选股信号列表
        """
        # 计算各类因子
        returns = market_data['close'].pct_change()
        
        # Beta值计算
        betas = self.factor_calculator.calculate_betas(
            pd.DataFrame({s: returns for s in market_data.index.get_level_values('symbol').unique()}),
            benchmark_returns,
            window=60
        )
        
        # 波动率计算
        volatility = self.factor_calculator.calculate_volatility(returns, window=20)
        
        # 成交活跃度
        daily_turnover = self._calculate_daily_turnover(market_data)
        
        # 60日涨幅
        return_60d = market_data['close'] / market_data['close'].shift(60) - 1
        
        # 获取因子数据
        symbols = market_data.index.get_level_values('symbol').unique()
        
        signals = []
        
        for symbol in symbols:
            try:
                # 获取该股票的因子值
                symbol_betas = betas.xs(symbol, level='symbol') if betas.index.nlevels > 1 else betas[symbol]
                symbol_volatility = volatility.xs(symbol, level='symbol') if volatility.index.nlevels > 1 else volatility[symbol]
                symbol_turnover = daily_turnover.xs(symbol, level='symbol') if daily_turnover.index.nlevels > 1 else daily_turnover[symbol]
                symbol_return = return_60d.xs(symbol, level='symbol') if return_60d.index.nlevels > 1 else return_60d[symbol]
                symbol_cap = market_data.xs(symbol, level='symbol')['market_cap'].iloc[-1]
                symbol_roe = market_data.xs(symbol, level='symbol')['roe'].iloc[-1]
                
                # 获取最新值
                beta = symbol_betas.iloc[-1] if len(symbol_betas) > 0 else np.nan
                vol = symbol_volatility.iloc[-1] if len(symbol_volatility) > 0 else np.nan
                turnover = symbol_turnover.iloc[-1] if len(symbol_turnover) > 0 else np.nan
                ret_60d = symbol_return.iloc[-1] if len(symbol_return) > 0 else np.nan
                
                # 基本面筛选
                if not self._basic_filter(beta, turnover, symbol_cap, ret_60d, symbol_roe):
                    continue
                
                # 计算综合得分
                score = self._calculate_score(beta, vol, turnover, ret_60d)
                
                signal = HighBetaSignal(
                    symbol=symbol,
                    beta=beta,
                    volatility=vol,
                    daily_turnover=turnover,
                    market_cap=symbol_cap,
                    return_60d=ret_60d,
                    roe=symbol_roe,
                    score=score
                )
                
                signals.append(signal)
                
            except Exception as e:
                continue
        
        # 按得分排序并筛选
        signals = sorted(signals, key=lambda x: x.score, reverse=True)
        
        # 筛选入选股票
        selected_count = 0
        sector_weights = {}
        
        for signal in signals:
            # 检查单股仓位限制
            if signal.score <= 0:
                continue
            
            # 获取行业信息（如果有）
            sector = self._get_sector(signal.symbol, market_data)
            
            # 检查行业仓位限制
            sector_weight = sector_weights.get(sector, 0)
            if sector_weight >= self.config['max_sector_position']:
                continue
            
            signal.is_selected = True
            selected_count += 1
            sector_weights[sector] = sector_weight + self.config['max_single_position']
            
            if selected_count >= 30:  # 最多选30只
                break
        
        return signals
    
    def _calculate_daily_turnover(self, market_data: pd.DataFrame) -> pd.Series:
        """
        计算日均成交额
        
        Args:
            market_data: 市场数据
            
        Returns:
            日均成交额序列
        """
        # 简化计算：收盘价 * 成交量
        turnover = market_data['close'] * market_data['volume']
        
        # 20日平均
        avg_turnover = turnover.rolling(window=20).mean()
        
        return avg_turnover
    
    def _basic_filter(self,
                       beta: float,
                       turnover: float,
                       market_cap: float,
                       return_60d: float,
                       roe: float) -> bool:
        """
        基本面筛选
        
        Args:
            beta: Beta值
            turnover: 日均成交额
            market_cap: 流通市值
            return_60d: 60日涨幅
            roe: ROE
            
        Returns:
            是否通过筛选
        """
        if np.isnan(beta):
            return False
        
        # Beta阈值
        if beta < self.config['beta_threshold']:
            return False
        
        # 流动性筛选
        if turnover < self.config['min_daily_turnover']:
            return False
        
        # 市值筛选
        if market_cap < self.config['min_market_cap'] or market_cap > self.config['max_market_cap']:
            return False
        
        # 趋势确认
        if return_60d < self.config['min_return_60d']:
            return False
        
        # 基本面底线
        if roe < self.config['min_roe']:
            return False
        
        return True
    
    def _calculate_score(self,
                          beta: float,
                          volatility: float,
                          turnover: float,
                          return_60d: float) -> float:
        """
        计算综合得分
        
        Args:
            beta: Beta值
            volatility: 波动率
            turnover: 成交活跃度
            return_60d: 60日涨幅
            
        Returns:
            综合得分
        """
        score = 0.0
        
        # Beta得分 (权重30%)
        if beta >= 2.0:
            score += 30.0
        elif beta >= 1.8:
            score += 25.0
        elif beta >= 1.5:
            score += 20.0
        else:
            score += (beta - 1.0) * 20  # 基础分
        
        # 波动率得分 (权重20%)
        if self.config['volatility_low'] <= volatility <= self.config['volatility_high']:
            score += 20.0
        else:
            score += 10.0
        
        # 成交活跃度得分 (权重15%)
        if turnover >= 10:
            score += 15.0
        elif turnover >= 5:
            score += 10.0
        else:
            score += 5.0
        
        # 趋势强度得分 (权重35%)
        if return_60d >= 0.5:
            score += 35.0
        elif return_60d >= 0.3:
            score += 30.0
        elif return_60d >= 0.2:
            score += 25.0
        elif return_60d >= 0.15:
            score += 20.0
        else:
            score += return_60d * 100
        
        return score
    
    def _get_sector(self, symbol: str, market_data: pd.DataFrame) -> str:
        """获取股票所在行业"""
        try:
            sector = market_data.xs(symbol, level='symbol')['sector'].iloc[-1]
            return sector
        except:
            return 'unknown'
    
    def get_target_position(self,
                            signals: List[HighBetaSignal],
                            market_stage: str = 'main_trend',
                            portfolio_value: float = 100000000) -> Dict[str, float]:
        """
        获取目标仓位
        
        Args:
            signals: 选股信号
            market_stage: 市场阶段
            portfolio_value: 组合价值
            
        Returns:
            目标仓位字典
        """
        # 根据市场阶段确定目标仓位
        stage_positions = {
            'startup': {'position': 0.70, 'leverage': 1.1},
            'main_trend': {'position': 0.90, 'leverage': 1.3},
            'diffusion': {'position': 0.70, 'leverage': 1.1},
            'ending': {'position': 0.40, 'leverage': 1.0}
        }
        
        stage_config = stage_positions.get(market_stage, stage_positions['main_trend'])
        
        # 筛选入选股票
        selected_signals = [s for s in signals if s.is_selected]
        
        if not selected_signals:
            return {}
        
        # 按得分分配权重
        total_score = sum(s.score for s in selected_signals)
        
        positions = {}
        for signal in selected_signals:
            # 基础权重
            weight = (signal.score / total_score) * stage_config['position']
            
            # 应用杠杆
            leveraged_weight = weight * stage_config['leverage']
            
            # 限制单股最大权重
            leveraged_weight = min(leveraged_weight, self.config['max_single_position'])
            
            positions[signal.symbol] = leveraged_weight
        
        # 归一化
        total_weight = sum(positions.values())
        if total_weight > 0:
            positions = {k: v / total_weight * stage_config['position'] 
                        for k, v in positions.items()}
        
        return positions
    
    def rebalance(self,
                  current_positions: Dict[str, float],
                  target_positions: Dict[str, float],
                  market_data: pd.DataFrame,
                  transaction_cost: float = 0.001) -> Tuple[Dict[str, float], float]:
        """
        调仓
        
        Args:
            current_positions: 当前仓位
            target_positions: 目标仓位
            market_data: 市场数据
            transaction_cost: 交易成本
            
        Returns:
            (调仓计划, 预估交易成本)
        """
        trades = {}
        total_cost = 0.0
        
        # 计算需要买入/卖出的股票
        all_symbols = set(current_positions.keys()) | set(target_positions.keys())
        
        for symbol in all_symbols:
            current = current_positions.get(symbol, 0.0)
            target = target_positions.get(symbol, 0.0)
            
            diff = target - current
            
            if abs(diff) > 0.005:  # 忽略小额变动
                trades[symbol] = diff
                total_cost += abs(diff) * transaction_cost
        
        return trades, total_cost
    
    def get_market_beta(self,
                        portfolio_returns: pd.Series,
                        benchmark_returns: pd.Series,
                        window: int = 60) -> float:
        """
        计算组合Beta
        
        Args:
            portfolio_returns: 组合收益率序列
            benchmark_returns: 基准收益率序列
            window: 计算窗口期
            
        Returns:
            组合Beta
        """
        beta = self.factor_calculator.calculate_beta(
            portfolio_returns,
            benchmark_returns,
            window
        )
        
        return beta.iloc[-1] if len(beta) > 0 else 1.0
    
    def calculate_contribution(self,
                                returns: pd.Series,
                                benchmark_returns: pd.Series) -> float:
        """
        计算策略收益贡献
        
        Args:
            returns: 策略收益率
            benchmark_returns: 基准收益率
            
        Returns:
            收益贡献
        """
        return returns.mean() - benchmark_returns.mean()
    
    def run_backtest(self,
                     data: pd.DataFrame,
                     benchmark_returns: pd.Series,
                     initial_capital: float = 1000000,
                     market_stage: str = 'main_trend') -> Dict:
        """
        运行回测
        
        Args:
            data: 历史数据
            benchmark_returns: 基准收益率
            initial_capital: 初始资金
            market_stage: 市场阶段
            
        Returns:
            回测结果
        """
        # 简化回测框架
        signals = self.select_stocks(data, benchmark_returns, market_stage)
        positions = self.get_target_position(signals, market_stage)
        
        return {
            'signals': signals,
            'positions': positions,
            'position_count': len(positions),
            'avg_beta': np.mean([s.beta for s in signals if s.is_selected]) if signals else 1.0
        }


# 便捷函数
def create_high_beta_strategy(config: Dict = None) -> HighBetaStrategy:
    """创建高Beta策略"""
    return HighBetaStrategy(config)


if __name__ == '__main__':
    # 简单测试
    strategy = HighBetaStrategy()
    print("高Beta策略模块加载成功")
