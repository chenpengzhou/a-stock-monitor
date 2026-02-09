"""
市场阶段检测器
================

用于识别牛市四阶段：启动期、主升期、扩散期、终结期

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from ..factors.factor_calculator import FactorCalculator


class MarketStage(Enum):
    """市场阶段"""
    STARTUP = "startup"        # 启动期
    MAIN_TREND = "main_trend"  # 主升期
    DIFFUSION = "diffusion"    # 扩散期
    ENDING = "ending"          # 终结期
    UNKNOWN = "unknown"        # 未知


@dataclass
class MarketIndicators:
    """市场指标"""
    # 成交量指标
    volume_ratio: float = 0.0           # 量比
    volume_trend: str = "neutral"       # 成交量趋势
    
    # 均线指标
    ma5_direction: str = "flat"         # 5日均线方向
    ma20_direction: str = "flat"         # 20日均线方向
    ma60_direction: str = "flat"        # 60日均线方向
    ma_status: str = "neutral"          # 均线状态
    
    # 动量指标
    momentum_20d: float = 0.0             # 20日动量
    momentum_60d: float = 0.0             # 60日动量
    momentum_trend: str = "neutral"      # 动量趋势
    
    # 涨跌停指标
    updown_ratio: float = 1.0            # 涨跌停比
    updown_trend: str = "neutral"        # 涨跌停趋势
    
    # 融资指标
    margin_growth: float = 0.0            # 融资余额增长率
    margin_trend: str = "neutral"        # 融资趋势
    
    # 综合得分
    overall_score: float = 50.0
    stage_confidence: float = 0.0        # 阶段判断置信度


class MarketStageDetector:
    """市场阶段检测器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化市场阶段检测器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
        self.factor_calculator = FactorCalculator()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 成交量参数
            'volume_base_multiplier': 1.5,
            'volume_accelerate_threshold': 2.0,
            
            # 均线参数
            'ma_trend_threshold': 0.02,
            
            # 动量参数
            'momentum_startup': 0.05,
            'momentum_main': 0.15,
            'momentum_diffusion': 0.10,
            
            # 涨跌停参数
            'updown_ratio_startup': 1.5,
            'updown_ratio_main': 3.0,
            'updown_ratio_ending': 0.5,
            
            # 融资参数
            'margin_growth_startup': 0.05,
            'margin_growth_main': 0.15,
            'margin_growth_ending': 0.02
        }
    
    def detect_market_stage(self,
                             index_data: pd.DataFrame,
                             market_stats: pd.DataFrame = None) -> Tuple[MarketStage, MarketIndicators]:
        """
        检测市场阶段
        
        Args:
            index_data: 指数数据 (包含close, volume等)
            market_stats: 市场统计数据 (包含涨跌停数量等)
            
        Returns:
            (市场阶段, 市场指标)
        """
        # 计算各类指标
        indicators = self._calculate_indicators(index_data, market_stats)
        
        # 综合判断
        stage, confidence = self._judge_stage(indicators)
        
        return stage, indicators
    
    def _calculate_indicators(self,
                               index_data: pd.DataFrame,
                               market_stats: pd.DataFrame = None) -> MarketIndicators:
        """
        计算市场指标
        
        Args:
            index_data: 指数数据
            market_stats: 市场统计数据
            
        Returns:
            市场指标
        """
        close = index_data['close']
        volume = index_data['volume']
        returns = close.pct_change()
        
        indicators = MarketIndicators()
        
        # 1. 成交量指标
        avg_volume = volume.rolling(20).mean()
        indicators.volume_ratio = (volume.iloc[-1] / avg_volume.iloc[-1]) if avg_volume.iloc[-1] > 0 else 1.0
        
        # 成交量趋势
        volume_ma5 = volume.rolling(5).mean()
        volume_ma20 = volume.rolling(20).mean()
        if volume_ma5.iloc[-1] > volume_ma20.iloc[-1] * 1.2:
            indicators.volume_trend = "increasing"
        elif volume_ma5.iloc[-1] < volume_ma20.iloc[-1] * 0.8:
            indicators.volume_trend = "decreasing"
        else:
            indicators.volume_trend = "stable"
        
        # 2. 均线指标
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()
        
        # 均线方向
        for name, ma in [('ma5', ma5), ('ma20', ma20), ('ma60', ma60)]:
            ma_change = ma.iloc[-1] / ma.iloc[-5] - 1 if len(ma) >= 5 else 0
            if ma_change > self.config['ma_trend_threshold']:
                direction = "up"
            elif ma_change < -self.config['ma_trend_threshold']:
                direction = "down"
            else:
                direction = "flat"
            
            if name == 'ma5':
                indicators.ma5_direction = direction
            elif name == 'ma20':
                indicators.ma20_direction = direction
            else:
                indicators.ma60_direction = direction
        
        # 均线状态
        if ma5.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1]:
            indicators.ma_status = "bullish"
        elif ma5.iloc[-1] < ma20.iloc[-1] < ma60.iloc[-1]:
            indicators.ma_status = "bearish"
        else:
            indicators.ma_status = "neutral"
        
        # 3. 动量指标
        indicators.momentum_20d = returns.rolling(20).sum().iloc[-1]
        indicators.momentum_60d = returns.rolling(60).sum().iloc[-1]
        
        # 动量趋势
        if indicators.momentum_20d > indicators.momentum_60d * 1.2:
            indicators.momentum_trend = "accelerating"
        elif indicators.momentum_20d < indicators.momentum_60d * 0.8:
            indicators.momentum_trend = "decelerating"
        else:
            indicators.momentum_trend = "stable"
        
        # 4. 涨跌停指标
        if market_stats is not None:
            up_limit = market_stats.get('up_limit', pd.Series([10]))
            down_limit = market_stats.get('down_limit', pd.Series([5]))
            
            up_count = up_limit.iloc[-5:].mean() if len(up_limit) >= 5 else 10
            down_count = down_limit.iloc[-5:].mean() if len(down_limit) >= 5 else 5
            
            indicators.updown_ratio = (up_count + 1) / (down_count + 1)
            
            # 涨跌停趋势
            up_trend = up_limit.iloc[-1] / up_limit.iloc[-5] - 1 if len(up_limit) >= 5 else 0
            down_trend = down_limit.iloc[-1] / down_limit.iloc[-5] - 1 if len(down_limit) >= 5 else 0
            
            if up_trend > 0.2 and down_trend < 0:
                indicators.updown_trend = "strong_bull"
            elif up_trend < -0.2 and down_trend > 0.2:
                indicators.updown_trend = "weak_bear"
            else:
                indicators.updown_trend = "neutral"
        
        # 5. 融资指标 (如果有数据)
        if 'margin_balance' in index_data.columns:
            margin = index_data['margin_balance']
            indicators.margin_growth = margin.pct_change(20).iloc[-1]
            
            if indicators.margin_growth > self.config['margin_growth_main']:
                indicators.margin_trend = "strong_inflow"
            elif indicators.margin_growth > self.config['margin_growth_startup']:
                indicators.margin_trend = "moderate_inflow"
            elif indicators.margin_growth > 0:
                indicators.margin_trend = "slow_inflow"
            else:
                indicators.margin_trend = "outflow"
        
        return indicators
    
    def _judge_stage(self,
                      indicators: MarketIndicators) -> Tuple[MarketStage, float]:
        """
        判断市场阶段
        
        Args:
            indicators: 市场指标
            
        Returns:
            (市场阶段, 置信度)
        """
        scores = {
            'startup': 0.0,
            'main_trend': 0.0,
            'diffusion': 0.0,
            'ending': 0.0
        }
        
        # 1. 成交量权重 (25%)
        if indicators.volume_trend == "increasing":
            if indicators.volume_ratio > 2.0:
                scores['main_trend'] += 20
                scores['diffusion'] += 15
            elif indicators.volume_ratio > 1.5:
                scores['startup'] += 15
                scores['main_trend'] += 15
            else:
                scores['startup'] += 10
        else:
            scores['ending'] += 15
        
        # 2. 均线状态权重 (25%)
        if indicators.ma_status == "bullish":
            scores['main_trend'] += 20
            scores['startup'] += 10
            scores['diffusion'] += 15
        elif indicators.ma_status == "bearish":
            scores['ending'] += 20
        else:
            scores['startup'] += 10
        
        # 3. 动量权重 (25%)
        if indicators.momentum_20d > self.config['momentum_main']:
            scores['main_trend'] += 20
            scores['diffusion'] += 15
        elif indicators.momentum_20d > self.config['momentum_startup']:
            scores['startup'] += 15
            scores['main_trend'] += 10
        elif indicators.momentum_20d > self.config['momentum_diffusion']:
            scores['diffusion'] += 20
        elif indicators.momentum_20d > 0:
            scores['ending'] += 10
        else:
            scores['ending'] += 20
        
        # 4. 涨跌停比权重 (15%)
        if indicators.updown_ratio > self.config['updown_ratio_main']:
            scores['main_trend'] += 15
            scores['diffusion'] += 10
        elif indicators.updown_ratio > self.config['updown_ratio_startup']:
            scores['startup'] += 10
            scores['main_trend'] += 5
        elif indicators.updown_ratio < self.config['updown_ratio_ending']:
            scores['ending'] += 15
        else:
            scores['diffusion'] += 10
        
        # 5. 融资趋势权重 (10%)
        if indicators.margin_trend in ["strong_inflow", "moderate_inflow"]:
            scores['main_trend'] += 10
            scores['diffusion'] += 5
        elif indicators.margin_trend == "slow_inflow":
            scores['startup'] += 5
        elif indicators.margin_trend == "outflow":
            scores['ending'] += 10
        
        # 综合得分
        total_score = sum(scores.values())
        if total_score > 0:
            indicators.overall_score = max(scores.values()) / total_score * 100
        
        # 确定阶段
        stage = max(scores.items(), key=lambda x: x[1])[0]
        
        # 置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            confidence = (sorted_scores[0] - sorted_scores[1]) / total_score * 100
        else:
            confidence = 100.0
        
        # 阶段映射
        stage_map = {
            'startup': MarketStage.STARTUP,
            'main_trend': MarketStage.MAIN_TREND,
            'diffusion': MarketStage.DIFFUSION,
            'ending': MarketStage.ENDING
        }
        
        return stage_map.get(stage, MarketStage.UNKNOWN), confidence
    
    def get_stage_position_config(self,
                                   stage: MarketStage) -> Dict:
        """
        获取阶段对应的仓位配置
        
        Args:
            stage: 市场阶段
            
        Returns:
            仓位配置
        """
        config_map = {
            MarketStage.STARTUP: {
                'beta_target': 1.8,
                'position': 0.70,
                'leverage': 1.1,
                'focus': ['金融', '券商', '银行']
            },
            MarketStage.MAIN_TREND: {
                'beta_target': 2.5,
                'position': 0.90,
                'leverage': 1.3,
                'focus': ['TMT', '电子', '计算机', '成长股']
            },
            MarketStage.DIFFUSION: {
                'beta_target': 1.8,
                'position': 0.70,
                'leverage': 1.1,
                'focus': ['新能源', '周期', '消费']
            },
            MarketStage.ENDING: {
                'beta_target': 1.1,
                'position': 0.40,
                'leverage': 1.0,
                'focus': ['防御', '公用事业', '银行']
            }
        }
        
        return config_map.get(stage, config_map[MarketStage.MAIN_TREND])
    
    def get_stage_description(self, stage: MarketStage) -> str:
        """
        获取阶段描述
        
        Args:
            stage: 市场阶段
            
        Returns:
            阶段描述
        """
        descriptions = {
            MarketStage.STARTUP: "启动期：市场情绪回暖，成交额开始放大，金融板块率先启动",
            MarketStage.MAIN_TREND: "主升期：趋势确认，量价齐升，成长风格领涨",
            MarketStage.DIFFUSION: "扩散期：热点扩散，低位板块补涨",
            MarketStage.ENDING: "终结期：滞涨股补涨完成，估值泡沫化，风险累积",
            MarketStage.UNKNOWN: "未知阶段"
        }
        
        return descriptions.get(stage, "未知阶段")
    
    def monitor_stage_transition(self,
                                  current_stage: MarketStage,
                                  new_indicators: MarketIndicators) -> Tuple[bool, str]:
        """
        监测阶段转换
        
        Args:
            current_stage: 当前阶段
            new_indicators: 新市场指标
            
        Returns:
            (是否发生阶段转换, 转换描述)
        """
        new_stage, confidence = self._judge_stage(new_indicators)
        
        if new_stage != current_stage:
            return True, f"{self.get_stage_description(current_stage)} → {self.get_stage_description(new_stage)}"
        
        return False, ""


# 便捷函数
def detect_market_stage(index_data: pd.DataFrame,
                         market_stats: pd.DataFrame = None) -> Tuple[MarketStage, MarketIndicators]:
    """检测市场阶段"""
    detector = MarketStageDetector()
    return detector.detect_market_stage(index_data, market_stats)


if __name__ == '__main__':
    detector = MarketStageDetector()
    print("市场阶段检测器加载成功")
