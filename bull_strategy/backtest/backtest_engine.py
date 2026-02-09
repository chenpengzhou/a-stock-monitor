"""
回测框架
=========

提供完整的回测功能：
- 历史数据模拟
- 策略信号生成
- 交易模拟执行
- 绩效评估分析

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x: x  # 如果没有安装tqdm，使用空实现
import json


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000      # 初始资金
    transaction_cost: float = 0.001        # 交易成本
    slippage: float = 0.001               # 滑点
    benchmark: str = '000300'             # 基准代码
    start_date: str = '20200101'          # 开始日期
    end_date: str = '20241231'            # 结束日期
    rebalance_freq: str = 'monthly'       # 调仓频率
    data_frequency: str = 'daily'          # 数据频率


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    symbol: str
    action: str  # buy/sell
    price: float
    quantity: float
    amount: float
    commission: float
    slippage: float
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class DailyRecord:
    """每日记录"""
    date: str
    portfolio_value: float
    cash: float
    positions_value: float
    daily_return: float
    cumulative_return: float
    benchmark_value: float
    benchmark_return: float
    excess_return: float


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 基本收益
    total_return: float = 0.0
    annualized_return: float = 0.0
    monthly_returns: List[float] = field(default_factory=list)
    
    # 风险指标
    volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # 交易统计
    total_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # 持仓统计
    avg_position_days: float = 0.0
    turnover_rate: float = 0.0


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig = None):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        self.config = config or BacktestConfig()
        
        # 状态变量
        self.data: pd.DataFrame = None
        self.benchmark_data: pd.Series = None
        self.trades: List[TradeRecord] = []
        self.daily_records: List[DailyRecord] = []
        self.positions: Dict[str, float] = {}
        self.cash: float = 0.0
        
        # 策略函数
        self.strategy_funcs: List[Callable] = []
    
    def load_data(self, data: pd.DataFrame, benchmark_data: pd.Series = None):
        """
        加载数据
        
        Args:
            data: 市场数据
            benchmark_data: 基准数据
        """
        self.data = data
        self.benchmark_data = benchmark_data
        
        # 初始化现金
        self.cash = self.config.initial_capital
    
    def add_strategy(self, func: Callable):
        """
        添加策略函数
        
        Args:
            func: 策略函数，接受日期，返回交易信号
        """
        self.strategy_funcs.append(func)
    
    def run_backtest(self) -> Tuple[PerformanceMetrics, List[DailyRecord], List[TradeRecord]]:
        """
        运行回测
        
        Returns:
            (绩效指标, 每日记录, 交易记录)
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        # 获取交易日列表
        dates = self.data.index.get_level_values('date').unique()
        
        # 初始化
        self.cash = self.config.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_records = []
        
        # 记录每日净值
        portfolio_value = self.cash
        benchmark_value = self.config.initial_capital
        
        prev_date = None
        
        for date in tqdm(dates, desc="回测进度"):
            try:
                # 获取当日数据
                day_data = self.data.xs(date, level='date')
                
                # 更新持仓市值
                positions_value = self._update_positions_value(day_data)
                
                # 计算当日收益率
                if len(self.daily_records) > 0:
                    prev_value = self.daily_records[-1].portfolio_value
                    if prev_value > 0:
                        daily_return = (positions_value + self.cash - prev_value) / prev_value
                    else:
                        daily_return = 0.0
                else:
                    daily_return = 0.0
                
                # 更新基准
                if self.benchmark_data is not None and date in self.benchmark_data.index:
                    benchmark_return = self.benchmark_data.loc[date] if isinstance(self.benchmark_data, pd.Series) else 0.0
                    benchmark_value *= (1 + benchmark_return)
                else:
                    benchmark_return = 0.0
                
                # 计算累计收益
                cumulative_return = (positions_value + self.cash) / self.config.initial_capital - 1
                
                # 记录每日
                self.daily_records.append(DailyRecord(
                    date=str(date),
                    portfolio_value=positions_value + self.cash,
                    cash=self.cash,
                    positions_value=positions_value,
                    daily_return=daily_return,
                    cumulative_return=cumulative_return,
                    benchmark_value=benchmark_value,
                    benchmark_return=benchmark_return,
                    excess_return=cumulative_return - (benchmark_value / self.config.initial_capital - 1)
                ))
                
                # 执行策略信号
                for func in self.strategy_funcs:
                    signals = func(date, self.data, self.positions, self.cash)
                    self._execute_signals(date, day_data, signals)
                
                prev_date = date
                
            except Exception as e:
                continue
        
        # 计算绩效指标
        metrics = self._calculate_performance()
        
        return metrics, self.daily_records, self.trades
    
    def _update_positions_value(self, day_data: pd.DataFrame) -> float:
        """
        更新持仓市值
        
        Args:
            day_data: 当日数据
            
        Returns:
            持仓总市值
        """
        total_value = 0.0
        
        for symbol, quantity in self.positions.items():
            try:
                if symbol in day_data.index.get_level_values('symbol'):
                    price = day_data.loc[symbol, 'close']
                    total_value += price * quantity
            except:
                continue
        
        return total_value
    
    def _execute_signals(self,
                         date,
                         day_data: pd.DataFrame,
                         signals: Dict[str, Dict]):
        """
        执行交易信号
        
        Args:
            date: 日期
            day_data: 当日数据
            signals: 信号字典 {symbol: {'action': 'buy'/'sell', 'weight': w}}
        """
        for symbol, signal in signals.items():
            action = signal.get('action', '')
            
            try:
                if symbol not in day_data.index.get_level_values('symbol'):
                    continue
                
                price = day_data.loc[symbol, 'close']
                
                if action == 'buy':
                    # 买入
                    available_cash = self.cash * 0.9  # 保留10%现金
                    amount = available_cash * signal.get('weight', 0.1)
                    quantity = amount / price / (1 + self.config.transaction_cost)
                    
                    if quantity > 0:
                        commission = amount * self.config.transaction_cost
                        slippage_amount = amount * self.config.slippage
                        
                        self.cash -= amount + commission + slippage_amount
                        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                        
                        self.trades.append(TradeRecord(
                            date=str(date),
                            symbol=symbol,
                            action='buy',
                            price=price,
                            quantity=quantity,
                            amount=amount,
                            commission=commission,
                            slippage=slippage_amount
                        ))
                
                elif action == 'sell':
                    # 卖出
                    if symbol in self.positions:
                        quantity = self.positions[symbol] * signal.get('weight', 1.0)
                        amount = quantity * price
                        
                        commission = amount * self.config.transaction_cost
                        slippage_amount = amount * self.config.slippage
                        
                        self.cash += amount - commission - slippage_amount
                        
                        self.trades.append(TradeRecord(
                            date=str(date),
                            symbol=symbol,
                            action='sell',
                            price=price,
                            quantity=quantity,
                            amount=amount,
                            commission=commission,
                            slippage=slippage_amount,
                            pnl=amount - commission - slippage_amount
                        ))
                        
                        self.positions[symbol] -= quantity
                        if self.positions[symbol] < 100:  # 清理零散持仓
                            del self.positions[symbol]
            
            except Exception as e:
                continue
    
    def _calculate_performance(self) -> PerformanceMetrics:
        """
        计算绩效指标
        
        Returns:
            绩效指标
        """
        metrics = PerformanceMetrics()
        
        if not self.daily_records:
            return metrics
        
        # 转换为DataFrame
        df = pd.DataFrame([r.__dict__ for r in self.daily_records])
        
        returns = df['daily_return'].dropna()
        
        # 基本收益
        total_value = df['portfolio_value'].iloc[-1]
        initial_value = self.config.initial_capital
        
        metrics.total_return = total_value / initial_value - 1
        trading_days = len(returns)
        metrics.annualized_return = (1 + metrics.total_return) ** (252 / trading_days) - 1
        
        # 月度收益
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly_returns = df.groupby('month')['daily_return'].apply(
            lambda x: (1 + x).prod() - 1
        )
        metrics.monthly_returns = monthly_returns.tolist()
        
        # 波动率
        metrics.volatility = returns.std() * np.sqrt(252)
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        metrics.max_drawdown = drawdown.min()
        
        # 回撤持续天数
        in_drawdown = False
        drawdown_days = 0
        max_duration = 0
        
        for dd in drawdown:
            if dd < 0:
                if not in_drawdown:
                    in_drawdown = True
                    current_duration = 0
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                in_drawdown = False
        
        metrics.max_drawdown_duration = max_duration
        
        # 风险调整收益
        risk_free_rate = 0.03 / 252
        
        if returns.std() > 0:
            metrics.sharpe_ratio = (returns.mean() - risk_free_rate) / returns.std() * np.sqrt(252)
        
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            metrics.sortino_ratio = (returns.mean() - risk_free_rate) / downside_returns.std() * np.sqrt(252)
        
        if abs(metrics.max_drawdown) > 0:
            metrics.calmar_ratio = metrics.annualized_return / abs(metrics.max_drawdown)
        
        # 交易统计
        metrics.total_trades = len(self.trades)
        
        if self.trades:
            sell_trades = [t for t in self.trades if t.action == 'sell']
            
            if sell_trades:
                profits = [t.pnl for t in sell_trades if t.pnl > 0]
                losses = [t.pnl for t in sell_trades if t.pnl < 0]
                
                wins = sum(1 for t in sell_trades if t.pnl > 0)
                total = len(sell_trades)
                
                metrics.win_rate = wins / total if total > 0 else 0
                metrics.avg_win = np.mean(profits) if profits else 0
                metrics.avg_loss = np.mean(losses) if losses else 0
                
                gross_profits = sum(profits) if profits else 0
                gross_losses = abs(sum(losses)) if losses else 1
                metrics.profit_factor = gross_profits / gross_losses if gross_losses > 0 else 0
        
        # 换手率
        if self.daily_records:
            avg_value = np.mean([r.portfolio_value for r in self.daily_records])
            total_volume = sum(t.amount for t in self.trades)
            metrics.turnover_rate = total_volume / avg_value / trading_days * 252 if avg_value > 0 else 0
        
        return metrics
    
    def generate_report(self,
                        metrics: PerformanceMetrics,
                        daily_records: List[DailyRecord],
                        trades: List[TradeRecord]) -> Dict:
        """
        生成回测报告
        
        Args:
            metrics: 绩效指标
            daily_records: 每日记录
            trades: 交易记录
            
        Returns:
            回测报告
        """
        report = {
            'config': self.config.__dict__,
            'performance': metrics.__dict__,
            'summary': {
                'total_return': f"{metrics.total_return:.2%}",
                'annualized_return': f"{metrics.annualized_return:.2%}",
                'volatility': f"{metrics.volatility:.2%}",
                'max_drawdown': f"{metrics.max_drawdown:.2%}",
                'sharpe_ratio': f"{metrics.sharpe_ratio:.2f}",
                'calmar_ratio': f"{metrics.calmar_ratio:.2f}",
                'win_rate': f"{metrics.win_rate:.2%}",
                'total_trades': metrics.total_trades,
                'profit_factor': f"{metrics.profit_factor:.2f}"
            },
            'trade_summary': {
                'total_trades': len(trades),
                'buy_trades': len([t for t in trades if t.action == 'buy']),
                'sell_trades': len([t for t in trades if t.action == 'sell']),
                'total_commission': sum(t.commission for t in trades),
                'total_slippage': sum(t.slippage for t in trades)
            },
            'monthly_returns': metrics.monthly_returns[:12] if len(metrics.monthly_returns) > 12 else metrics.monthly_returns
        }
        
        return report
    
    def save_results(self,
                     metrics: PerformanceMetrics,
                     daily_records: List[DailyRecord],
                     trades: List[TradeRecord],
                     filepath: str):
        """
        保存回测结果
        
        Args:
            metrics: 绩效指标
            daily_records: 每日记录
            trades: 交易记录
            filepath: 保存路径
        """
        report = self.generate_report(metrics, daily_records, trades)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def plot_results(self,
                     daily_records: List[DailyRecord],
                     show: bool = True,
                     save_path: str = None):
        """
        绘制回测结果
        
        Args:
            daily_records: 每日记录
            show: 是否显示
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            df = pd.DataFrame([r.__dict__ for r in daily_records])
            df['date'] = pd.to_datetime(df['date'])
            
            fig, axes = plt.subplots(3, 2, figsize=(14, 10))
            
            # 净值曲线
            ax1 = axes[0, 0]
            ax1.plot(df['date'], df['portfolio_value'], label='Portfolio')
            ax1.plot(df['date'], df['benchmark_value'], label='Benchmark')
            ax1.set_title('Portfolio Value')
            ax1.legend()
            ax1.grid(True)
            
            # 累计收益
            ax2 = axes[0, 1]
            ax2.plot(df['date'], df['cumulative_return'] * 100, label='Portfolio')
            ax2.plot(df['date'], df['excess_return'] * 100, label='Excess')
            ax2.set_title('Cumulative Return (%)')
            ax2.legend()
            ax2.grid(True)
            
            # 回撤
            ax3 = axes[1, 0]
            cumulative = (1 + df['daily_return'].fillna(0)).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative - rolling_max) / rolling_max * 100
            ax3.fill_between(df['date'], drawdown, 0, color='red', alpha=0.3)
            ax3.set_title('Drawdown (%)')
            ax3.grid(True)
            
            # 月度收益
            ax4 = axes[1, 1]
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            monthly = df.groupby('month')['daily_return'].apply(lambda x: (1 + x).prod() - 1) * 100
            monthly.plot(kind='bar', ax=ax4, color=['green' if x > 0 else 'red' for x in monthly])
            ax4.set_title('Monthly Returns (%)')
            ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(True)
            
            # 收益分布
            ax5 = axes[2, 0]
            ax5.hist(df['daily_return'].dropna() * 100, bins=50, edgecolor='black')
            ax5.set_title('Daily Return Distribution (%)')
            ax5.axvline(x=0, color='red', linestyle='--')
            ax5.grid(True)
            
            # 胜率统计
            ax6 = axes[2, 1]
            returns = df['daily_return'].dropna()
            win_rate = (returns > 0).sum() / len(returns) * 100
            loss_rate = (returns < 0).sum() / len(returns) * 100
            ax6.pie([win_rate, loss_rate], labels=['Win', 'Loss'], autopct='%1.1f%%',
                   colors=['green', 'red'])
            ax6.set_title('Win Rate')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
            
            if show:
                plt.show()
            
        except ImportError:
            print("需要安装matplotlib才能绘图")
    
    def optimize_parameters(self,
                           param_grid: Dict,
                           metric: str = 'sharpe_ratio') -> Dict:
        """
        参数优化
        
        Args:
            param_grid: 参数网格
            metric: 优化目标指标
            
        Returns:
            最优参数
        """
        from itertools import product
        
        best_params = None
        best_value = -np.inf
        
        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(product(*param_grid.values()))
        
        for params in param_values:
            # 设置参数
            param_dict = dict(zip(param_names, params))
            
            # 重新运行回测
            self.config = BacktestConfig(**{**self.config.__dict__, **param_dict})
            metrics, _, _ = self.run_backtest()
            
            # 获取优化目标
            value = getattr(metrics, metric, 0)
            
            if value > best_value:
                best_value = value
                best_params = param_dict
        
        return best_params


# 便捷函数
def create_backtest_engine(config: BacktestConfig = None) -> BacktestEngine:
    """创建回测引擎"""
    return BacktestEngine(config)


if __name__ == '__main__':
    engine = create_backtest_engine()
    print("回测引擎加载成功")
