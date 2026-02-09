"""
风险管理器
==========

提供全面的风险管理功能：
- 事前风控：仓位限制、分散度控制
- 事中风控：止损机制、止盈机制、回撤控制
- 事后风控：业绩归因、风险复盘

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class AlertType(Enum):
    """预警类型"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    POSITION_LIMIT = "position_limit"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"


@dataclass
class RiskMetrics:
    """风险指标"""
    # 基本风险指标
    total_exposure: float = 0.0           # 总敞口
    net_exposure: float = 0.0             # 净敞口
    gross_exposure: float = 0.0           # 总仓位
    
    # 波动率指标
    portfolio_volatility: float = 0.0     # 组合波动率
    benchmark_volatility: float = 0.0     # 基准波动率
    
    # 回撤指标
    current_drawdown: float = 0.0         # 当前回撤
    max_drawdown: float = 0.0             # 最大回撤
    drawdown_duration: int = 0             # 回撤持续天数
    
    # 收益指标
    total_return: float = 0.0              # 总收益率
    annualized_return: float = 0.0        # 年化收益率
    excess_return: float = 0.0           # 超额收益
    
    # 风险调整收益
    sharpe_ratio: float = 0.0            # 夏普比率
    sortino_ratio: float = 0.0           # 索提诺比率
    calmar_ratio: float = 0.0            # 卡玛比率
    information_ratio: float = 0.0       # 信息比率
    
    # VaR指标
    var_95: float = 0.0                   # 95% VaR
    var_99: float = 0.0                   # 99% VaR
    
    # 风险等级
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass
class RiskAlert:
    """风险预警"""
    alert_type: AlertType
    severity: str  # info/warning/error/critical
    message: str
    timestamp: str
    current_value: float = 0.0
    threshold_value: float = 0.0
    recommended_action: str = ""


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化风险管理器
        
        Args:
            config: 风险配置
        """
        self.config = config or self._default_config()
        
        # 状态变量
        self.alerts: List[RiskAlert] = []
        self.positions: Dict[str, float] = {}
        self.portfolio_history: List[Dict] = []
        
        # 峰值记录
        self.peak_value: float = 0.0
        self.drawdown_history: List[float] = []
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 仓位限制
            'max_single_position': 0.05,       # 单股最大仓位
            'max_sector_position': 0.35,      # 单板块最大仓位
            'max_strategy_position': 0.60,    # 单策略最大仓位
            'max_portfolio_position': 1.0,    # 组合最大仓位
            
            # 杠杆限制
            'max_leverage': 1.3,               # 最大杠杆
            
            # 波动率限制
            'max_volatility': 0.45,           # 最大年化波动率
            'volatility_threshold': 0.35,     # 波动率预警阈值
            
            # 回撤限制
            'max_drawdown': 0.25,             # 最大回撤
            'drawdown_warning': 0.15,         # 回撤预警阈值
            'drawdown_stop': 0.20,           # 回撤止损线
            
            # 止损止盈
            'stop_loss': 0.10,                # 单股止损线
            'take_profit': 0.50,             # 单股止盈线
            'trailing_stop': 0.05,           # 跟踪止损
            
            # 流动性限制
            'min_daily_turnover': 3.0,        # 最小日均成交额(亿元)
            'max_position_liquidity': 0.02,   # 仓位占日成交额比例上限
            
            # 分散度要求
            'min_stock_count': 10,            # 最少持股数量
            'max_correlation': 0.8,           # 持仓间最大相关系数
        }
    
    # ==================== 事前风控 ====================
    
    def check_position_limits(self,
                             positions: Dict[str, Dict],
                             sectors: Dict[str, List[str]] = None) -> List[RiskAlert]:
        """
        检查仓位限制
        
        Args:
            positions: 持仓字典 {symbol: {'weight': w, 'sector': s}}
            sectors: 板块映射
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        for symbol, pos in positions.items():
            weight = pos.get('weight', 0)
            
            # 单股仓位检查
            if weight > self.config['max_single_position']:
                alerts.append(RiskAlert(
                    alert_type=AlertType.POSITION_LIMIT,
                    severity='warning' if weight < self.config['max_single_position'] * 1.5 else 'error',
                    message=f"单股{symbol}仓位{weight:.1%}超过限制{self.config['max_single_position']:.1%}",
                    timestamp=datetime.now().isoformat(),
                    current_value=weight,
                    threshold_value=self.config['max_single_position'],
                    recommended_action=f"减仓{symbol}至{self.config['max_single_position']:.1%}"
                ))
        
        # 板块仓位检查
        if sectors:
            sector_weights = {}
            for symbol, pos in positions.items():
                sector = pos.get('sector', 'unknown')
                sector_weights[sector] = sector_weights.get(sector, 0) + pos.get('weight', 0)
            
            for sector, weight in sector_weights.items():
                if weight > self.config['max_sector_position']:
                    alerts.append(RiskAlert(
                        alert_type=AlertType.POSITION_LIMIT,
                        severity='warning',
                        message=f"板块{sector}权重{weight:.1%}超过限制{self.config['max_sector_position']:.1%}",
                        timestamp=datetime.now().isoformat(),
                        current_value=weight,
                        threshold_value=self.config['max_sector_position'],
                        recommended_action=f"减仓{sector}相关股票"
                    ))
        
        return alerts
    
    def check_leverage_limit(self,
                             total_exposure: float,
                             net_exposure: float,
                             capital: float) -> List[RiskAlert]:
        """
        检查杠杆限制
        
        Args:
            total_exposure: 总敞口
            net_exposure: 净敞口
            capital: 资本金
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        leverage = total_exposure / capital
        
        if leverage > self.config['max_leverage']:
            alerts.append(RiskAlert(
                alert_type=AlertType.LEVERAGE,
                severity='critical',
                message=f"杠杆{leverage:.2f}超过限制{self.config['max_leverage']:.2f}",
                timestamp=datetime.now().isoformat(),
                current_value=leverage,
                threshold_value=self.config['max_leverage'],
                recommended_action="立即降杠杆"
            ))
        elif leverage > self.config['max_leverage'] * 0.9:
            alerts.append(RiskAlert(
                alert_type=AlertType.LEVERAGE,
                severity='warning',
                message=f"杠杆{leverage:.2f}接近限制{self.config['max_leverage']:.2f}",
                timestamp=datetime.now().isoformat(),
                current_value=leverage,
                threshold_value=self.config['max_leverage'],
                recommended_action="准备降杠杆"
            ))
        
        return alerts
    
    def check_liquidity(self,
                         positions: Dict[str, Dict],
                         daily_turnover: Dict[str, float]) -> List[RiskAlert]:
        """
        检查流动性
        
        Args:
            positions: 持仓字典
            daily_turnover: 日均成交额字典
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        for symbol, pos in positions.items():
            weight = pos.get('weight', 0)
            turnover = daily_turnover.get(symbol, 0)
            
            if turnover < self.config['min_daily_turnover']:
                alerts.append(RiskAlert(
                    alert_type=AlertType.LIQUIDITY,
                    severity='warning',
                    message=f"股票{symbol}流动性不足，日成交{turnover:.1f}亿 < {self.config['min_daily_turnover']:.1f}亿",
                    timestamp=datetime.now().isoformat(),
                    current_value=turnover,
                    threshold_value=self.config['min_daily_turnover'],
                    recommended_action=f"考虑减持{symbol}"
                ))
            
            # 检查仓位占比
            position_value = weight * 100  # 假设组合100万
            if turnover > 0 and position_value / turnover > self.config['max_position_liquidity']:
                alerts.append(RiskAlert(
                    alert_type=AlertType.LIQUIDITY,
                    severity='warning',
                    message=f"股票{symbol}仓位{position_value:.1f}万占日成交{turnover:.1f}亿比例过高",
                    timestamp=datetime.now().isoformat(),
                    current_value=position_value / turnover / 10000,
                    threshold_value=self.config['max_position_liquidity'],
                    recommended_action=f"注意{symbol}流动性风险"
                ))
        
        return alerts
    
    # ==================== 事中风控 ====================
    
    def calculate_stop_loss(self,
                             entry_price: float,
                             current_price: float,
                             atr: float = None) -> float:
        """
        计算止损价
        
        Args:
            entry_price: 入场价
            current_price: 当前价
            atr: ATR值
            
        Returns:
            止损价
        """
        if atr:
            # ATR止损
            stop_price = current_price - 2 * atr
        else:
            # 百分比止损
            stop_price = entry_price * (1 - self.config['stop_loss'])
        
        return stop_price
    
    def calculate_take_profit(self,
                              entry_price: float,
                              current_price: float,
                              atr: float = None) -> float:
        """
        计算止盈价
        
        Args:
            entry_price: 入场价
            current_price: 当前价
            atr: ATR值
            
        Returns:
            止盈价
        """
        if atr:
            # ATR止盈
            stop_price = current_price + 3 * atr
        else:
            # 目标价止盈
            stop_price = entry_price * (1 + self.config['take_profit'])
        
        return stop_price
    
    def calculate_trailing_stop(self,
                                 entry_price: float,
                                 current_price: float,
                                 peak_price: float = None) -> float:
        """
        计算跟踪止损价
        
        Args:
            entry_price: 入场价
            current_price: 当前价
            peak_price: 峰值价
            
        Returns:
            跟踪止损价
        """
        peak = peak_price if peak_price else current_price
        trailing_stop = peak * (1 - self.config['trailing_stop'])
        
        # 确保不低于入场价
        return max(trailing_stop, entry_price * (1 - self.config['stop_loss']))
    
    def check_stop_loss_trigger(self,
                                symbol: str,
                                current_price: float,
                                entry_price: float,
                                positions: Dict[str, float]) -> Tuple[bool, str]:
        """
        检查是否触发止损
        
        Args:
            symbol: 股票代码
            current_price: 当前价
            entry_price: 入场价
            positions: 持仓字典
            
        Returns:
            (是否触发, 触发原因)
        """
        if symbol not in positions:
            return False, ""
        
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct < -self.config['stop_loss']:
            return True, f"止损触发，亏损{pnl_pct:.1%}"
        
        return False, ""
    
    def check_take_profit_trigger(self,
                                   symbol: str,
                                   current_price: float,
                                   entry_price: float,
                                   positions: Dict[str, float]) -> Tuple[bool, str]:
        """
        检查是否触发止盈
        
        Args:
            symbol: 股票代码
            current_price: 当前价
            entry_price: 入场价
            positions: 持仓字典
            
        Returns:
            (是否触发, 触发原因)
        """
        if symbol not in positions:
            return False, ""
        
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct > self.config['take_profit']:
            return True, f"止盈触发，盈利{pnl_pct:.1%}"
        
        return False, ""
    
    def calculate_drawdown(self,
                           portfolio_values: pd.Series) -> Tuple[float, float, int]:
        """
        计算回撤
        
        Args:
            portfolio_values: 组合价值序列
            
        Returns:
            (当前回撤, 最大回撤, 回撤持续天数)
        """
        # 计算累计最大值
        running_max = portfolio_values.cummax()
        
        # 计算回撤
        drawdown = (portfolio_values - running_max) / running_max
        
        current_drawdown = drawdown.iloc[-1]
        max_drawdown = drawdown.min()
        
        # 计算回撤持续天数
        drawdown_duration = 0
        in_drawdown = False
        
        for d in reversed(drawdown.values):
            if d < 0:
                if not in_drawdown:
                    in_drawdown = True
                drawdown_duration += 1
            else:
                if in_drawdown:
                    break
        
        return current_drawdown, max_drawdown, drawdown_duration
    
    def check_drawdown_alert(self,
                             current_drawdown: float,
                             max_drawdown: float) -> List[RiskAlert]:
        """
        检查回撤预警
        
        Args:
            current_drawdown: 当前回撤
            max_drawdown: 最大回撤
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        if abs(current_drawdown) > self.config['drawdown_stop']:
            alerts.append(RiskAlert(
                alert_type=AlertType.DRAWDOWN,
                severity='critical',
                message=f"回撤达到{abs(current_drawdown):.1%}，触发止损线{self.config['drawdown_stop']:.1%}",
                timestamp=datetime.now().isoformat(),
                current_value=current_drawdown,
                threshold_value=-self.config['drawdown_stop'],
                recommended_action="减仓50%防御"
            ))
        elif abs(current_drawdown) > self.config['drawdown_warning']:
            alerts.append(RiskAlert(
                alert_type=AlertType.DRAWDOWN,
                severity='warning',
                message=f"回撤达到{abs(current_drawdown):.1%}，接近止损线{self.config['drawdown_stop']:.1%}",
                timestamp=datetime.now().isoformat(),
                current_value=current_drawdown,
                threshold_value=-self.config['drawdown_warning'],
                recommended_action="关注风险，准备减仓"
            ))
        elif abs(max_drawdown) > self.config['max_drawdown']:
            alerts.append(RiskAlert(
                alert_type=AlertType.DRAWDOWN,
                severity='warning',
                message=f"历史最大回撤{max_drawdown:.1%}超过限制{self.config['max_drawdown']:.1%}",
                timestamp=datetime.now().isoformat(),
                current_value=max_drawdown,
                threshold_value=-self.config['max_drawdown'],
                recommended_action="复盘策略，降低风险敞口"
            ))
        
        return alerts
    
    def check_volatility_alert(self,
                                portfolio_volatility: float) -> List[RiskAlert]:
        """
        检查波动率预警
        
        Args:
            portfolio_volatility: 组合波动率
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        if portfolio_volatility > self.config['max_volatility']:
            alerts.append(RiskAlert(
                alert_type=AlertType.VOLATILITY,
                severity='critical',
                message=f"波动率{portfolio_volatility:.1%}超过限制{self.config['max_volatility']:.1%}",
                timestamp=datetime.now().isoformat(),
                current_value=portfolio_volatility,
                threshold_value=self.config['max_volatility'],
                recommended_action="降低仓位或持有低波资产"
            ))
        elif portfolio_volatility > self.config['volatility_threshold']:
            alerts.append(RiskAlert(
                alert_type=AlertType.VOLATILITY,
                severity='warning',
                message=f"波动率{portfolio_volatility:.1%}接近限制{self.config['max_volatility']:.1%}",
                timestamp=datetime.now().isoformat(),
                current_value=portfolio_volatility,
                threshold_value=self.config['volatility_threshold'],
                recommended_action="监控波动率，准备调整"
            ))
        
        return alerts
    
    # ==================== 风险指标计算 ====================
    
    def calculate_risk_metrics(self,
                               portfolio_returns: pd.Series,
                               benchmark_returns: pd.Series,
                               risk_free_rate: float = 0.03) -> RiskMetrics:
        """
        计算风险指标
        
        Args:
            portfolio_returns: 组合收益率序列
            benchmark_returns: 基准收益率序列
            risk_free_rate: 无风险利率
            
        Returns:
            风险指标
        """
        metrics = RiskMetrics()
        
        # 基本收益指标
        metrics.total_return = (1 + portfolio_returns).prod() - 1
        metrics.annualized_return = (1 + metrics.total_return) ** (252 / len(portfolio_returns)) - 1
        metrics.excess_return = metrics.annualized_return - risk_free_rate
        
        # 波动率
        metrics.portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
        metrics.benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
        
        # 夏普比率
        excess_returns = portfolio_returns - risk_free_rate / 252
        metrics.sharpe_ratio = excess_returns.mean() / portfolio_returns.std() * np.sqrt(252) \
            if portfolio_returns.std() > 0 else 0
        
        # 回撤
        portfolio_values = (1 + portfolio_returns).cumprod()
        current_dd, max_dd, duration = self.calculate_drawdown(portfolio_values)
        metrics.current_drawdown = current_dd
        metrics.max_drawdown = max_dd
        metrics.drawdown_duration = duration
        
        # 卡玛比率
        if abs(max_dd) > 0:
            metrics.calmar_ratio = metrics.annualized_return / abs(max_dd)
        else:
            metrics.calmar_ratio = 0
        
        # VaR (简化计算)
        metrics.var_95 = np.percentile(portfolio_returns, 5)
        metrics.var_99 = np.percentile(portfolio_returns, 1)
        
        # 信息比率
        tracking_error = (portfolio_returns - benchmark_returns).std() * np.sqrt(252)
        if tracking_error > 0:
            metrics.information_ratio = (metrics.excess_return) / tracking_error
        else:
            metrics.information_ratio = 0
        
        # 风险等级
        if metrics.sharpe_ratio > 1.5 and abs(metrics.max_drawdown) < 0.15:
            metrics.risk_level = RiskLevel.LOW
        elif metrics.sharpe_ratio > 1.0 and abs(metrics.max_drawdown) < 0.25:
            metrics.risk_level = RiskLevel.MEDIUM
        elif metrics.sharpe_ratio > 0.5 and abs(metrics.max_drawdown) < 0.35:
            metrics.risk_level = RiskLevel.HIGH
        else:
            metrics.risk_level = RiskLevel.EXTREME
        
        return metrics
    
    # ==================== 策略执行 ====================
    
    def before_trade(self,
                     positions: Dict[str, Dict],
                     sectors: Dict[str, List[str]] = None,
                     daily_turnover: Dict[str, float] = None) -> Tuple[bool, List[RiskAlert]]:
        """
        交易前风控检查
        
        Args:
            positions: 目标持仓
            sectors: 板块映射
            daily_turnover: 日均成交额
            
        Returns:
            (是否通过检查, 风险预警列表)
        """
        alerts = []
        
        # 检查仓位限制
        alerts.extend(self.check_position_limits(positions, sectors))
        
        # 检查流动性
        if daily_turnover:
            alerts.extend(self.check_liquidity(positions, daily_turnover))
        
        # 判断是否通过
        critical_alerts = [a for a in alerts if a.severity == 'critical']
        
        passed = len(critical_alerts) == 0
        
        return passed, alerts
    
    def during_trade(self,
                     portfolio_values: pd.Series,
                     portfolio_volatility: float) -> List[RiskAlert]:
        """
        交易中风控检查
        
        Args:
            portfolio_values: 组合价值序列
            portfolio_volatility: 组合波动率
            
        Returns:
            风险预警列表
        """
        alerts = []
        
        # 更新峰值
        current_value = portfolio_values.iloc[-1]
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # 计算回撤
        current_dd, max_dd, _ = self.calculate_drawdown(portfolio_values)
        
        # 检查回撤
        alerts.extend(self.check_drawdown_alert(current_dd, max_dd))
        
        # 检查波动率
        alerts.extend(self.check_volatility_alert(portfolio_volatility))
        
        # 记录回撤历史
        self.drawdown_history.append(current_dd)
        
        return alerts
    
    def after_trade(self,
                    returns: pd.Series,
                    benchmark_returns: pd.Series) -> Dict:
        """
        交易后风控分析
        
        Args:
            returns: 组合收益率
            benchmark_returns: 基准收益率
            
        Returns:
            风控分析报告
        """
        metrics = self.calculate_risk_metrics(returns, benchmark_returns)
        
        return {
            'metrics': metrics.__dict__,
            'alerts': [a.__dict__ for a in self.alerts],
            'recommendations': self._generate_recommendations(metrics)
        }
    
    def _generate_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """
        生成风控建议
        
        Args:
            metrics: 风险指标
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if metrics.risk_level == RiskLevel.EXTREME:
            recommendations.append("风险过高，建议大幅降低仓位")
            recommendations.append("暂停新开仓，逐步减仓")
        elif metrics.risk_level == RiskLevel.HIGH:
            recommendations.append("风险偏高，建议适度降低仓位")
            recommendations.append("关注波动率变化，准备调整")
        
        if abs(metrics.max_drawdown) > 0.2:
            recommendations.append("历史回撤较大，建议增加止损机制")
        
        if metrics.sharpe_ratio < 1.0:
            recommendations.append("夏普比率偏低，建议优化选股策略")
        
        if metrics.calmar_ratio < 3:
            recommendations.append("卡玛比率偏低，建议增加防御仓位")
        
        return recommendations
    
    def emergency_stop(self) -> Dict:
        """
        紧急止损
        
        Returns:
            止损方案
        """
        return {
            'action': 'emergency_stop',
            'position_reduction': 0.5,
            'keep_positions': ['高Beta', '防御板块'],
            'liquidity_action': '保留现金',
            'reason': '触发紧急止损条件'
        }


# 便捷函数
def create_risk_manager(config: Dict = None) -> RiskManager:
    """创建风险管理器"""
    return RiskManager(config)


if __name__ == '__main__':
    manager = RiskManager()
    print("风险管理器加载成功")
