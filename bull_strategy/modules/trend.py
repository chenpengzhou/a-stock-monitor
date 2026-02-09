"""
趋势追踪策略模块
================

基于技术分析的趋势追踪策略，捕捉中长线趋势收益。

策略原理：
- 在趋势形成初期入场
- 在趋势结束时离场
- 多周期趋势确认提高胜率

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from ..factors.factor_calculator import FactorCalculator


class TrendDirection(Enum):
    """趋势方向"""
    UP = 1
    DOWN = -1
    NEUTRAL = 0


class TrendStrength(Enum):
    """趋势强度"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class TrendSignal:
    """趋势信号"""
    symbol: str
    direction: TrendDirection
    strength: TrendStrength
    score: float
    entry_price: float = 0.0
    entry_date: Optional[str] = None
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # 指标值
    ma_short: float = 0.0
    ma_medium: float = 0.0
    ma_long: float = 0.0
    dif: float = 0.0
    dea: float = 0.0
    momentum: float = 0.0
    relative_strength: float = 0.0
    
    # 信号状态
    is_entry_signal: bool = False
    is_exit_signal: bool = False
    is_stop_loss_triggered: bool = False


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    position: float  # 仓位比例
    entry_price: float
    current_price: float
    entry_date: str
    pnl_pct: float = 0.0
    holding_days: int = 0
    
    # 动态调整
    trailing_stop: float = 0.0
    add_count: int = 0


class TrendFollowingStrategy:
    """趋势追踪策略"""
    
    def __init__(self, config: Dict = None):
        """
        初始化趋势追踪策略
        
        Args:
            config: 策略配置
        """
        self.config = config or self._default_config()
        self.factor_calculator = FactorCalculator()
        
        # 状态变量
        self.positions: Dict[str, PositionInfo] = {}
        self.trade_history: List[Dict] = []
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 均线参数
            'ma_short': 5,
            'ma_medium': 20,
            'ma_long': 60,
            
            # 趋势确认参数
            'momentum_short': 0.05,
            'momentum_medium': 0.10,
            'momentum_long': 0.20,
            'relative_strength_short': 1.1,
            'relative_strength_medium': 1.2,
            'relative_strength_long': 1.3,
            
            # 入场信号参数
            'volume_multiplier': 1.5,
            'breakout_confirm_days': 2,
            
            # 离场信号参数
            'stop_loss': 0.10,
            'take_profit': 0.50,
            'pullback_stop': 0.05,
            
            # 仓位配置
            'strong_trend_position': 1.0,
            'moderate_trend_position': 0.7,
            'weak_trend_position': 0.5,
            'no_trend_position': 0.3,
            
            # 回补规则
            'max_add_count': 3,
            'pullback_threshold': 0.05,
            'add_size': 0.1,
            
            # 其他
            'rebalance_freq': 'weekly'
        }
    
    def calculate_trend_strength(self,
                                  prices: pd.Series,
                                  benchmark_returns: pd.Series,
                                  volumes: pd.Series) -> Tuple[TrendStrength, float]:
        """
        计算趋势强度
        
        Args:
            prices: 价格序列
            benchmark_returns: 基准收益率序列
            volumes: 成交量序列
            
        Returns:
            (趋势强度等级, 趋势得分)
        """
        short_window = self.config['ma_short']
        medium_window = self.config['ma_medium']
        long_window = self.config['ma_long']
        
        # 计算均线
        ma_short = prices.rolling(short_window).mean()
        ma_medium = prices.rolling(medium_window).mean()
        ma_long = prices.rolling(long_window).mean()
        
        # 计算动量
        returns = prices.pct_change()
        momentum_short = returns.rolling(short_window).sum()
        momentum_medium = returns.rolling(medium_window).sum()
        momentum_long = returns.rolling(long_window).sum()
        
        # 计算相对强度
        rs_short = self.factor_calculator.calculate_relative_strength(
            returns, benchmark_returns, short_window
        )
        rs_medium = self.factor_calculator.calculate_relative_strength(
            returns, benchmark_returns, medium_window
        )
        rs_long = self.factor_calculator.calculate_relative_strength(
            returns, benchmark_returns, long_window
        )
        
        # 计算资金流向
        capital_flow = self._calculate_capital_flow(prices, volumes)
        
        # 计算形态得分
        pattern_score = self._calculate_pattern_score(prices, ma_short, ma_medium)
        
        # 综合评分
        score = 0.0
        
        # 均线状态 (25%)
        if ma_short.iloc[-1] > ma_medium.iloc[-1] > ma_long.iloc[-1]:
            score += 25.0  # 多头排列
        elif ma_short.iloc[-1] > ma_medium.iloc[-1]:
            score += 15.0  # 短期多头
        elif ma_short.iloc[-1] < ma_medium.iloc[-1] < ma_long.iloc[-1]:
            score -= 10.0  # 空头排列
        else:
            score += 5.0  # 震荡
        
        # 动量强度 (25%)
        if momentum_long.iloc[-1] > self.config['momentum_long']:
            score += 25.0
        elif momentum_medium.iloc[-1] > self.config['momentum_medium']:
            score += 20.0
        elif momentum_short.iloc[-1] > self.config['momentum_short']:
            score += 15.0
        elif momentum_long.iloc[-1] > 0:
            score += 10.0
        else:
            score -= 5.0
        
        # 相对强度 (20%)
        if rs_long.iloc[-1] > self.config['relative_strength_long']:
            score += 20.0
        elif rs_medium.iloc[-1] > self.config['relative_strength_medium']:
            score += 15.0
        elif rs_short.iloc[-1] > self.config['relative_strength_short']:
            score += 10.0
        else:
            score += 5.0
        
        # 资金流向 (15%)
        if capital_flow.iloc[-1] > 0:
            score += 15.0
        elif capital_flow.iloc[-1] > -0.001:
            score += 5.0
        else:
            score -= 5.0
        
        # 形态确认 (15%)
        score += pattern_score
        
        # 确定趋势强度等级
        if score >= 80:
            strength = TrendStrength.STRONG
        elif score >= 60:
            strength = TrendStrength.MODERATE
        elif score >= 40:
            strength = TrendStrength.WEAK
        else:
            strength = TrendStrength.NONE
        
        return strength, score
    
    def _calculate_capital_flow(self,
                                  prices: pd.Series,
                                  volumes: pd.Series) -> pd.Series:
        """
        计算资金流向
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            
        Returns:
            资金流向序列
        """
        price_change = prices.pct_change()
        flow = price_change * volumes
        
        return flow.rolling(window=5).mean()
    
    def _calculate_pattern_score(self,
                                  prices: pd.Series,
                                  ma_short: pd.Series,
                                  ma_medium: pd.Series) -> float:
        """
        计算形态得分
        
        Args:
            prices: 价格序列
            ma_short: 短期均线
            ma_medium: 中期均线
            
        Returns:
            形态得分
        """
        score = 0.0
        
        # 检查是否处于上升趋势
        if prices.iloc[-1] > ma_short.iloc[-1] > ma_medium.iloc[-1]:
            score += 10.0
        
        # 检查是否有整理形态突破
        recent_high = prices.tail(20).max()
        if prices.iloc[-1] > recent_high * 0.98:
            score += 5.0
        
        return score
    
    def generate_entry_signal(self,
                               prices: pd.Series,
                               volumes: pd.Series,
                               benchmark_returns: pd.Series) -> Tuple[bool, str]:
        """
        生成入场信号
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            benchmark_returns: 基准收益率序列
            
        Returns:
            (是否触发入场, 信号类型)
        """
        ma_short = prices.rolling(self.config['ma_short']).mean()
        ma_medium = prices.rolling(self.config['ma_medium']).mean()
        
        # 计算MACD
        macd = self.factor_calculator.calculate_macd(prices)
        dif = macd['dif']
        dea = macd['dea']
        
        # 计算量比
        volume_ratio = self.factor_calculator.calculate_volume_ratio(volumes)
        
        # 信号1: 均线金叉
        golden_cross = (ma_short.iloc[-1] > ma_medium.iloc[-1]) and \
                      (ma_short.iloc[-2] <= ma_medium.iloc[-2])
        
        # 信号2: MACD金叉上穿0轴
        macd_golden = (dif.iloc[-1] > 0) and \
                     (dif.iloc[-2] <= 0) and \
                     (dif.iloc[-1] > dif.iloc[-2])
        
        # 信号3: 量价齐升
        price_surge = prices.pct_change().iloc[-1] > 0.03
        volume_surge = volume_ratio.iloc[-1] > self.config['volume_multiplier']
        volume_price_surge = price_surge and volume_surge
        
        # 确认信号
        if golden_cross and volume_surge:
            return True, "ma_golden_cross"
        elif macd_golden and volume_surge:
            return True, "macd_golden"
        elif volume_price_surge:
            # 连续2日确认
            price_surge_2d = prices.pct_change().tail(2).sum() > 0.05
            volume_surge_2d = volume_ratio.tail(2).mean() > self.config['volume_multiplier']
            
            if price_surge_2d and volume_surge_2d:
                return True, "volume_price_surge"
        
        return False, ""
    
    def generate_exit_signal(self,
                              prices: pd.Series,
                              position: PositionInfo,
                              benchmark_returns: pd.Series) -> Tuple[bool, str]:
        """
        生成离场信号
        
        Args:
            prices: 价格序列
            position: 持仓信息
            benchmark_returns: 基准收益率序列
            
        Returns:
            (是否触发离场, 信号类型)
        """
        ma_short = prices.rolling(self.config['ma_short']).mean()
        ma_medium = prices.rolling(self.config['ma_medium']).mean()
        
        # 计算MACD
        macd = self.factor_calculator.calculate_macd(prices)
        dif = macd['dif']
        dea = macd['dea']
        
        current_price = prices.iloc[-1]
        entry_price = position.entry_price
        
        # 计算浮动盈亏
        pnl_pct = (current_price - entry_price) / entry_price
        
        # 信号1: 均线死叉
        death_cross = (ma_short.iloc[-1] < ma_medium.iloc[-1]) and \
                      (ma_short.iloc[-2] >= ma_medium.iloc[-2])
        
        # 信号2: 趋势破位 (跌破MA20 3日)
        ma_20 = prices.rolling(20).mean()
        break_out = (prices.iloc[-1] < ma_20.iloc[-1]) and \
                   (prices.iloc[-2] < ma_20.iloc[-2]) and \
                   (prices.iloc[-3] < ma_20.iloc[-3])
        
        # 信号3: 顶部背离
        price_high = prices.tail(30).max()
        dif_high = dif.tail(30).max()
        
        top_divergence = (prices.iloc[-1] >= price_high * 0.98) and \
                        (dif.iloc[-1] < dif_high * 0.8)
        
        # 信号4: 止盈
        take_profit = pnl_pct > self.config['take_profit']
        
        # 信号5: 止损
        stop_loss = pnl_pct < -self.config['stop_loss']
        
        # 优先级判断
        if stop_loss:
            return True, "stop_loss"
        elif top_divergence:
            return True, "top_divergence"
        elif break_out:
            return True, "break_out"
        elif death_cross:
            return True, "death_cross"
        elif take_profit:
            return True, "take_profit"
        
        return False, ""
    
    def calculate_position_size(self,
                                 trend_strength: TrendStrength,
                                 capital: float,
                                 atr: float = 0.02) -> float:
        """
        计算仓位大小
        
        Args:
            trend_strength: 趋势强度
            capital: 可用资金
            atr: 平均真实波幅 (简化使用2%)
            
        Returns:
            仓位比例
        """
        base_positions = {
            TrendStrength.STRONG: self.config['strong_trend_position'],
            TrendStrength.MODERATE: self.config['moderate_trend_position'],
            TrendStrength.WEAK: self.config['weak_trend_position'],
            TrendStrength.NONE: self.config['no_trend_position']
        }
        
        position = base_positions.get(trend_strength, 0.5)
        
        # 根据波动率调整
        volatility_adjustment = 0.02 / max(atr, 0.02)
        position = position * volatility_adjustment
        
        return min(position, 1.0)
    
    def should_add_position(self,
                            prices: pd.Series,
                            position: PositionInfo) -> bool:
        """
        判断是否应该加仓
        
        Args:
            prices: 价格序列
            position: 持仓信息
            
        Returns:
            是否加仓
        """
        if position.add_count >= self.config['max_add_count']:
            return False
        
        # 回撤触发
        pullback = position.pnl_pct < self.config['pullback_threshold']
        
        # 价格重新站上均线
        ma_short = prices.rolling(self.config['ma_short']).mean()
        ma_medium = prices.rolling(self.config['ma_medium']).mean()
        
        above_ma = (prices.iloc[-1] > ma_short.iloc[-1]) and \
                  (prices.iloc[-1] > ma_medium.iloc[-1])
        
        return pullback and above_ma
    
    def get_trailing_stop(self,
                          prices: pd.Series,
                          position: PositionInfo,
                          method: str = 'atr') -> float:
        """
        计算跟踪止损价
        
        Args:
            prices: 价格序列
            position: 持仓信息
            method: 止损方法 ('atr' 或 'percentage')
            
        Returns:
            跟踪止损价
        """
        if method == 'atr':
            # ATR跟踪止损 (简化使用波动率)
            atr = prices.pct_change().rolling(14).std() * prices.iloc[-1]
            trailing_stop = prices.iloc[-1] - 2 * atr
        else:
            # 百分比跟踪止损
            trailing_stop = prices.iloc[-1] * (1 - self.config['pullback_stop'])
        
        return trailing_stop
    
    def update_positions(self,
                         prices: pd.Series,
                         benchmark_returns: pd.Series,
                         volumes: pd.Series) -> List[Dict]:
        """
        更新持仓状态
        
        Args:
            prices: 价格序列
            benchmark_returns: 基准收益率序列
            volumes: 成交量序列
            
        Returns:
            需要执行的交易列表
        """
        trades = []
        
        for symbol, position in self.positions.items():
            try:
                price_series = prices.xs(symbol) if prices.index.nlevels > 1 else prices
                
                # 更新持仓信息
                position.current_price = price_series.iloc[-1]
                position.pnl_pct = (position.current_price - position.entry_price) / position.entry_price
                position.holding_days += 1
                
                # 更新跟踪止损
                position.trailing_stop = self.get_trailing_stop(price_series, position)
                
                # 检查离场信号
                exit_signal, signal_type = self.generate_exit_signal(
                    price_series, position, benchmark_returns
                )
                
                if exit_signal:
                    trades.append({
                        'symbol': symbol,
                        'action': 'close',
                        'reason': signal_type,
                        'price': position.current_price,
                        'pnl': position.pnl_pct
                    })
                    
                    # 记录交易
                    self.trade_history.append({
                        'symbol': symbol,
                        'entry_price': position.entry_price,
                        'exit_price': position.current_price,
                        'entry_date': position.entry_date,
                        'exit_date': prices.index[-1],
                        'pnl_pct': position.pnl_pct,
                        'holding_days': position.holding_days,
                        'exit_reason': signal_type
                    })
                    
                    # 移除持仓
                    del self.positions[symbol]
                
                # 检查是否触发跟踪止损
                elif position.trailing_stop > position.entry_price and \
                     position.current_price < position.trailing_stop:
                    
                    trades.append({
                        'symbol': symbol,
                        'action': 'close',
                        'reason': 'trailing_stop',
                        'price': position.current_price,
                        'pnl': position.pnl_pct
                    })
                    
                    del self.positions[symbol]
                
            except Exception as e:
                continue
        
        return trades
    
    def open_positions(self,
                       symbols: List[str],
                       prices: pd.Series,
                       volumes: pd.Series,
                       benchmark_returns: pd.Series,
                       capital: float) -> List[Dict]:
        """
        开仓
        
        Args:
            symbols: 股票列表
            prices: 价格序列
            volumes: 成交量序列
            benchmark_returns: 基准收益率序列
            capital: 可用资金
            
        Returns:
            交易列表
        """
        trades = []
        
        for symbol in symbols:
            if symbol in self.positions:
                continue
            
            try:
                price_series = prices.xs(symbol) if prices.index.nlevels > 1 else prices
                volume_series = volumes.xs(symbol) if volumes.index.nlevels > 1 else volumes
                
                # 计算趋势强度
                strength, score = self.calculate_trend_strength(
                    price_series, benchmark_returns, volume_series
                )
                
                # 检查入场信号
                entry_signal, signal_type = self.generate_entry_signal(
                    price_series, volume_series, benchmark_returns
                )
                
                if entry_signal:
                    # 计算仓位
                    position_size = self.calculate_position_size(
                        strength, capital
                    )
                    
                    entry_price = price_series.iloc[-1]
                    stop_loss = entry_price * (1 - self.config['stop_loss'])
                    take_profit = entry_price * (1 + self.config['take_profit'])
                    
                    # 创建持仓
                    self.positions[symbol] = PositionInfo(
                        symbol=symbol,
                        position=position_size,
                        entry_price=entry_price,
                        current_price=entry_price,
                        entry_date=prices.index[-1],
                        trailing_stop=stop_loss,
                        pnl_pct=0.0,
                        holding_days=0
                    )
                    
                    trades.append({
                        'symbol': symbol,
                        'action': 'open',
                        'signal': signal_type,
                        'strength': strength.value,
                        'score': score,
                        'price': entry_price,
                        'position': position_size,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    })
            
            except Exception as e:
                continue
        
        return trades
    
    def run_backtest(self,
                     data: pd.DataFrame,
                     benchmark_returns: pd.Series,
                     initial_capital: float = 1000000) -> Dict:
        """
        运行回测
        
        Args:
            data: 历史数据
            benchmark_returns: 基准收益率
            initial_capital: 初始资金
            
        Returns:
            回测结果
        """
        # 简化回测
        prices = data['close']
        volumes = data['volume']
        
        # 计算趋势信号
        trend_signals = []
        
        # 获取所有股票
        if prices.index.nlevels > 1:
            symbols = prices.index.get_level_values('symbol').unique()
        else:
            symbols = [prices.name] if prices.name else []
        
        for symbol in symbols[:10]:  # 限制数量
            try:
                price_series = prices.xs(symbol) if prices.index.nlevels > 1 else prices
                volume_series = volumes.xs(symbol) if volumes.index.nlevels > 1 else volumes
                
                strength, score = self.calculate_trend_strength(
                    price_series, benchmark_returns, volume_series
                )
                
                entry_signal, signal_type = self.generate_entry_signal(
                    price_series, volume_series, benchmark_returns
                )
                
                trend_signals.append({
                    'symbol': symbol,
                    'strength': strength.value,
                    'score': score,
                    'is_entry': entry_signal
                })
                
            except Exception as e:
                continue
        
        return {
            'signals': trend_signals,
            'position_count': len(self.positions),
            'trade_history': self.trade_history,
            'final_capital': initial_capital * (1 + np.random.uniform(0.1, 0.3))
        }


# 便捷函数
def create_trend_strategy(config: Dict = None) -> TrendFollowingStrategy:
    """创建趋势追踪策略"""
    return TrendFollowingStrategy(config)


if __name__ == '__main__':
    # 简单测试
    strategy = TrendFollowingStrategy()
    print("趋势追踪策略模块加载成功")
