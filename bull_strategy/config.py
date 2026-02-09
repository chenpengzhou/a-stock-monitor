"""
牛市高倍收益策略配置参数
=========================

Author: OpenClaw
Date: 2026-02-09
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json


@dataclass
class HighBetaConfig:
    """高Beta策略配置"""
    beta_threshold: float = 1.5          # Beta阈值
    min_daily_turnover: float = 5.0      # 最小日均成交额(亿元)
    min_market_cap: float = 100.0        # 最小流通市值(亿元)
    max_market_cap: float = 2000.0       # 最大流通市值(亿元)
    min_return_60d: float = 0.15         # 60日最小涨幅
    min_roe: float = 0.10                # 最小ROE
    volatility_range: tuple = (0.30, 0.80) # 波动率范围
    
    # 仓位配置
    startup_position: float = 0.70       # 启动期仓位
    main_trend_position: float = 0.90     # 主升期仓位
    diffusion_position: float = 0.70     # 扩散期仓位
    ending_position: float = 0.40         # 终结期仓位
    
    # 杠杆配置
    startup_leverage: float = 1.1
    main_trend_leverage: float = 1.3
    diffusion_leverage: float = 1.1
    ending_leverage: float = 1.0
    
    # 调仓配置
    rebalance_freq: str = 'monthly'       # 调仓频率
    max_single_position: float = 0.05     # 单股最大仓位
    max_sector_position: float = 0.35     # 单板块最大仓位


@dataclass
class TrendConfig:
    """趋势追踪策略配置"""
    ma_short: int = 5                     # 短期均线周期
    ma_medium: int = 20                   # 中期均线周期
    ma_long: int = 60                     # 长期均线周期
    
    # 趋势确认参数
    momentum_short: float = 0.05          # 5日动量阈值
    momentum_medium: float = 0.10         # 20日动量阈值
    momentum_long: float = 0.20            # 60日动量阈值
    relative_strength_short: float = 1.1  # 短期相对强度
    relative_strength_medium: float = 1.2 # 中期相对强度
    relative_strength_long: float = 1.3   # 长期相对强度
    
    # 入场信号参数
    volume_multiplier: float = 1.5         # 成交量放大倍数
    breakout_confirm_days: int = 2         # 突破确认天数
    
    # 离场信号参数
    stop_loss: float = 0.10                # 止损线
    take_profit: float = 0.50              # 止盈线
    pullback_stop: float = 0.05            # 回撤止盈线
    
    # 仓位配置
    strong_trend_position: float = 1.0     # 强趋势仓位
    moderate_trend_position: float = 0.7   # 中趋势仓位
    weak_trend_position: float = 0.5       # 弱趋势仓位
    no_trend_position: float = 0.3         # 无趋势仓位
    
    # 回补规则
    max_add_count: int = 3                 # 最大回补次数
    pullback_threshold: float = 0.05      # 回补触发阈值
    add_size: float = 0.1                  # 每次回补比例


@dataclass
class SectorRotationConfig:
    """板块轮动策略配置"""
    rebalance_freq: str = 'weekly'         # 调仓频率
    top_n_sectors: int = 3                 # 选取前N板块
    backup_n_sectors: int = 3              # 备选板块数
    
    # 评分因子权重
    momentum_20d_weight: float = 0.25      # 20日涨幅权重
    momentum_60d_weight: float = 0.15      # 60日涨幅权重
    capital_flow_weight: float = 0.20      # 资金流向权重
    margin_change_weight: float = 0.10      # 融资变化权重
    turnover_change_weight: float = 0.10   # 换手率变化权重
    updown_ratio_weight: float = 0.10     # 涨跌停比权重
    pe_percentile_weight: float = 0.05     # PE分位权重
    earnings_revision_weight: float = 0.05 # 盈利预测调整权重
    
    # 仓位限制
    max_sector_weight: float = 0.35        # 单板块最大权重
    min_sector_weight: float = 0.05         # 单板块最小权重
    min_correlation: float = 0.7            # 最小相关系数（分散化）
    
    # 轮动触发阈值
    rank_drop_threshold: int = 5            # 排名下降阈值
    leader_excess_return: float = 0.50      # 领先超额收益阈值
    new_sector_strength: float = 85.0      # 新强势板块阈值
    market_sentiment_threshold: float = 40.0 # 市场情绪阈值


@dataclass
class GrowthStockConfig:
    """成长股精选策略配置"""
    # 成长因子阈值
    min_revenue_cagr: float = 0.25         # 最小营收CAGR
    min_profit_cagr: float = 0.30           # 最小净利润CAGR
    min_roe: float = 0.15                   # 最小ROE
    min_gross_margin: float = 0.30          # 最小毛利率
    min_cash_flow_ratio: float = 0.80       # 经营现金流/净利润
    min_rd_expense_ratio: float = 0.05      # 研发费用占比
    
    # 盈利惊喜
    min_earnings_surprise: int = 5          # 最少超预期次数
    total_quarters: int = 8                 # 统计季度数
    
    # 估值参数
    base_pe: float = 15.0                   # 基础PE
    peg_undersold: float = 0.8              # 严重低估PEG
    peg_fair_low: float = 1.0               # 合理偏低PEG
    peg_fair_high: float = 1.5              # 合理偏高PEG
    peg_overvalued: float = 2.0              # 严重高估PEG
    
    # 仓位调整
    severely_undersold_add: float = 0.20     # 严重低估加仓
    fairly_low_maintain: float = 0.0         # 合理偏低维持
    fairly_high_reduce: float = -0.10        # 合理偏高减仓
    severely_overvalued_reduce: float = -0.30 # 严重高估减仓
    
    # 精选流程配置
    max_candidates: int = 200               # 初筛数量
    deep_research_count: int = 50           # 深度研究数量
    final_selection_count: int = 20          # 最终精选数量
    portfolio_size: int = 15                 # 最终组合数量
    
    # 分散化配置
    max_single_stock: float = 0.05           # 单股最大权重
    max_sector_concentration: float = 0.30   # 行业集中度上限


class StrategyConfig:
    """策略总配置"""
    
    def __init__(self):
        self.high_beta = HighBetaConfig()
        self.trend = TrendConfig()
        self.sector_rotation = SectorRotationConfig()
        self.growth = GrowthStockConfig()
        
        # 策略权重配置
        self.strategy_weights = {
            'high_beta': 0.30,
            'trend': 0.25,
            'sector_rotation': 0.25,
            'growth': 0.20
        }
        
        # 风控配置
        self.risk_config = {
            'max_portfolio_volatility': 0.45,      # 最大组合波动率
            'max_drawdown': 0.25,                  # 最大回撤
            'stop_loss': 0.10,                      # 单股止损
            'position_limit': 0.60,                # 策略整体仓位上限
            'liquidity_threshold': 3.0,             # 流动性阈值(亿元)
            'leverage_limit': 1.3                   # 杠杆上限
        }
        
        # 牛市阶段判断参数
        self.market_stage_params = {
            'volume_base_multiplier': 1.5,         # 成交量放大倍数
            'ma_trend_threshold': 0.05,             # 均线趋势阈值
            'financing_growth_threshold': 0.10      # 融资增长阈值
        }
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'high_beta': self.high_beta.__dict__,
            'trend': self.trend.__dict__,
            'sector_rotation': self.sector_rotation.__dict__,
            'growth': self.growth.__dict__,
            'strategy_weights': self.strategy_weights,
            'risk_config': self.risk_config,
            'market_stage_params': self.market_stage_params
        }
    
    def save(self, filepath: str):
        """保存配置到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'StrategyConfig':
        """从JSON文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls()
        config.high_beta = HighBetaConfig(**data.get('high_beta', {}))
        config.trend = TrendConfig(**data.get('trend', {}))
        config.sector_rotation = SectorRotationConfig(**data.get('sector_rotation', {}))
        config.growth = GrowthStockConfig(**data.get('growth', {}))
        config.strategy_weights = data.get('strategy_weights', config.strategy_weights)
        config.risk_config = data.get('risk_config', config.risk_config)
        config.market_stage_params = data.get('market_stage_params', config.market_stage_params)
        
        return config


# 默认配置实例
default_config = StrategyConfig()
