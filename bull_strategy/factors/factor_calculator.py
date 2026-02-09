"""
因子计算器 - 因子计算模块
===========================

提供各类因子的计算方法：
- Beta因子
- 动量因子
- 趋势因子
- 成长因子
- 资金流向因子

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FactorResult:
    """因子计算结果"""
    factor_name: str
    values: pd.Series
    normalized_values: Optional[pd.Series] = None
    percentiles: Optional[pd.Series] = None


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化因子计算器
        
        Args:
            risk_free_rate: 年化无风险利率
        """
        self.risk_free_rate = risk_free_rate
    
    # ==================== Beta因子计算 ====================
    
    def calculate_beta(self, 
                       returns: pd.Series, 
                       benchmark_returns: pd.Series,
                       window: int = 60) -> pd.Series:
        """
        计算Beta值
        
        Beta = Cov(ri, rm) / Var(rm)
        
        Args:
            returns: 资产收益率序列
            benchmark_returns: 基准收益率序列
            window: 计算窗口期
            
        Returns:
            Beta值序列
        """
        # 使用滚动窗口计算
        rolling_cov = returns.rolling(window=window).cov(benchmark_returns)
        rolling_var = benchmark_returns.rolling(window=window).var()
        
        beta = rolling_cov / rolling_var
        beta = beta.replace([np.inf, -np.inf], np.nan)
        
        return beta
    
    def calculate_betas(self, 
                        returns_df: pd.DataFrame, 
                        benchmark_returns: pd.Series,
                        window: int = 60) -> pd.DataFrame:
        """
        批量计算多资产Beta值
        
        Args:
            returns_df: 多资产收益率DataFrame
            benchmark_returns: 基准收益率序列
            window: 计算窗口期
            
        Returns:
            多资产Beta值DataFrame
        """
        betas = pd.DataFrame(index=returns_df.index)
        
        for col in returns_df.columns:
            betas[col] = self.calculate_beta(
                returns_df[col], 
                benchmark_returns, 
                window
            )
        
        return betas
    
    # ==================== 波动率因子计算 ====================
    
    def calculate_volatility(self, 
                             returns: pd.Series, 
                             window: int = 20,
                             annualize: bool = True) -> pd.Series:
        """
        计算波动率
        
        Args:
            returns: 收益率序列
            window: 计算窗口期
            annualize: 是否年化
            
        Returns:
            波动率序列
        """
        vol = returns.rolling(window=window).std()
        
        if annualize:
            # 日波动率年化 (假设252个交易日)
            vol = vol * np.sqrt(252)
        
        return vol
    
    def calculate_volatility_range(self,
                                   returns_df: pd.DataFrame,
                                   window: int = 20,
                                   low_percentile: float = 30,
                                   high_percentile: float = 80) -> Tuple[pd.Series, pd.Series]:
        """
        计算波动率分位区间
        
        Args:
            returns_df: 多资产收益率DataFrame
            window: 计算窗口期
            low_percentile: 低分位数阈值
            high_percentile: 高分位数阈值
            
        Returns:
            (低波动率阈值, 高波动率阈值)
        """
        vol_df = self.calculate_volatility(returns_df, window)
        
        low_threshold = vol_df.quantile(low_percentile / 100, axis=1)
        high_threshold = vol_df.quantile(high_percentile / 100, axis=1)
        
        return low_threshold, high_threshold
    
    # ==================== 动量因子计算 ====================
    
    def calculate_momentum(self, 
                          prices: pd.Series, 
                          periods: List[int] = [5, 20, 60, 120]) -> pd.DataFrame:
        """
        计算动量因子
        
        动量 = (P_t / P_{t-n}) - 1
        
        Args:
            prices: 价格序列
            periods: 计算周期列表
            
        Returns:
            多周期动量DataFrame
        """
        momentum = pd.DataFrame(index=prices.index)
        
        for period in periods:
            momentum[f'momentum_{period}d'] = prices / prices.shift(period) - 1
        
        return momentum
    
    def calculate_relative_strength(self,
                                    returns: pd.Series,
                                    benchmark_returns: pd.Series,
                                    window: int = 20) -> pd.Series:
        """
        计算相对强度
        
        相对强度 = 累计收益率 / 基准累计收益率
        
        Args:
            returns: 资产收益率序列
            benchmark_returns: 基准收益率序列
            window: 计算窗口期
            
        Returns:
            相对强度序列
        ”
        """
        asset_cum_return = (1 + returns.rolling(window=window)).prod() - 1
        benchmark_cum_return = (1 + benchmark_returns.rolling(window=window)).prod() - 1
        
        rs = (1 + asset_cum_return) / (1 + benchmark_cum_return)
        
        return rs
    
    def calculate_momentum_trend(self,
                                 momentum: pd.Series,
                                 window: int = 5) -> pd.Series:
        """
        计算动量趋势（动量斜率）
        
        Args:
            momentum: 动量因子序列
            window: 计算窗口期
            
        Returns:
            动量趋势序列
        """
        return momentum.rolling(window=window).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0,
            raw=True
        )
    
    # ==================== 趋势因子计算 ====================
    
    def calculate_moving_averages(self,
                                  prices: pd.Series,
                                  windows: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            prices: 价格序列
            windows: 窗口期列表
            
        Returns:
            多周期均线DataFrame
        """
        ma = pd.DataFrame(index=prices.index)
        
        for window in windows:
            ma[f'ma_{window}d'] = prices.rolling(window=window).mean()
        
        return ma
    
    def calculate_ma_trend(self,
                           prices: pd.Series,
                           short_window: int = 5,
                           long_window: int = 20) -> pd.Series:
        """
        计算均线趋势状态
        
        Returns:
            趋势状态: 1=多头, 0=震荡, -1=空头
        """
        ma_short = prices.rolling(short_window).mean()
        ma_long = prices.rolling(long_window).mean()
        
        trend = pd.Series(0, index=prices.index)
        trend[ma_short > ma_long] = 1
        trend[ma_short < ma_long] = -1
        
        return trend
    
    def calculate_golden_cross(self,
                                prices: pd.Series,
                                short_window: int = 5,
                                long_window: int = 20) -> pd.Series:
        """
        计算金叉/死叉信号
        
        Returns:
            信号序列: 1=金叉, -1=死叉, 0=无信号
        """
        ma_short = prices.rolling(short_window).mean()
        ma_long = prices.rolling(long_window).mean()
        
        signal = pd.Series(0, index=prices.index)
        
        # 金叉
        golden = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
        signal[golden] = 1
        
        # 死叉
        death = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))
        signal[death] = -1
        
        return signal
    
    # ==================== MACD因子计算 ====================
    
    def calculate_macd(self,
                       prices: pd.Series,
                       fast: int = 12,
                       slow: int = 26,
                       signal: int = 9) -> pd.DataFrame:
        """
        计算MACD
        
        Args:
            prices: 价格序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACD DataFrame (包含DIF, DEA, MACD柱)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_hist = (dif - dea) * 2
        
        return pd.DataFrame({
            'dif': dif,
            'dea': dea,
            'macd_hist': macd_hist
        })
    
    def calculate_macd_signal(self,
                               macd_df: pd.DataFrame) -> pd.Series:
        """
        计算MACD信号
        
        Returns:
            信号序列: 1=DIF上穿0轴, -1=DIF下穿0轴, 0=无信号
        """
        dif = macd_df['dif']
        
        signal = pd.Series(0, index=dif.index)
        
        # 上穿0轴
        golden = (dif > 0) & (dif.shift(1) <= 0)
        signal[golden] = 1
        
        # 下穿0轴
        death = (dif < 0) & (dif.shift(1) >= 0)
        signal[death] = -1
        
        return signal
    
    # ==================== 成长因子计算 ====================
    
    def calculate_cagr(self,
                       values: pd.Series,
                       periods: int) -> float:
        """
        计算复合年增长率 (CAGR)
        
        CAGR = (V_end / V_start)^(1/n) - 1
        
        Args:
            values: 价值序列
            periods: 年数
            
        Returns:
            CAGR值
        """
        if len(values) < 2 or values.iloc[0] <= 0:
            return np.nan
        
        start_value = values.iloc[0]
        end_value = values.iloc[-1]
        
        if start_value <= 0 or end_value <= 0:
            return np.nan
        
        cagr = (end_value / start_value) ** (1 / periods) - 1
        
        return cagr
    
    def calculate_revenue_cagr(self,
                               revenue_series: pd.Series,
                               years: int = 2) -> float:
        """
        计算营收CAGR
        
        Args:
            revenue_series: 营收序列（从远到近）
            years: 年数
            
        Returns:
            营收CAGR
        """
        return self.calculate_cagr(revenue_series, years)
    
    def calculate_profit_cagr(self,
                               profit_series: pd.Series,
                               years: int = 2) -> float:
        """
        计算净利润CAGR
        
        Args:
            profit_series: 净利润序列
            years: 年数
            
        Returns:
            净利润CAGR
        """
        return self.calculate_cagr(profit_series, years)
    
    def calculate_roe(self,
                     net_profit: float,
                     shareholders_equity: float) -> float:
        """
        计算ROE
        
        ROE = 净利润 / 净资产
        
        Args:
            net_profit: 净利润
            shareholders_equity: 净资产
            
        Returns:
            ROE
        """
        if shareholders_equity <= 0:
            return np.nan
        
        return net_profit / shareholders_equity
    
    def calculate_gross_margin(self,
                                revenue: float,
                                cost: float) -> float:
        """
        计算毛利率
        
        毛利率 = (营收 - 成本) / 营收
        
        Args:
            revenue: 营收
            cost: 成本
            
        Returns:
            毛利率
        """
        if revenue <= 0:
            return np.nan
        
        return (revenue - cost) / revenue
    
    def calculate_cash_flow_ratio(self,
                                   operating_cash_flow: float,
                                   net_profit: float) -> float:
        """
        计算经营现金流/净利润
        
        Args:
            operating_cash_flow: 经营性现金流
            net_profit: 净利润
            
        Returns:
            现金流比率
        """
        if net_profit <= 0:
            return np.nan
        
        return operating_cash_flow / net_profit
    
    def calculate_earnings_surprise(self,
                                     actual_earnings: pd.Series,
                                     expected_earnings: pd.Series) -> pd.Series:
        """
        计算盈利惊喜
        
        盈利惊喜 = (实际盈利 - 预期盈利) / |预期盈利|
        
        Args:
            actual_earnings: 实际盈利序列
            expected_earnings: 预期盈利序列
            
        Returns:
            盈利惊喜序列
        """
        surprise = (actual_earnings - expected_earnings) / expected_earnings.abs()
        surprise = surprise.replace([np.inf, -np.inf], np.nan)
        
        return surprise
    
    def calculate_surprise_count(self,
                                  surprise: pd.Series,
                                  threshold: float = 0.0) -> int:
        """
        计算超预期次数
        
        Args:
            surprise: 盈利惊喜序列
            threshold: 阈值（>0表示超预期）
            
        Returns:
            超预期次数
        """
        return (surprise > threshold).sum()
    
    def calculate_rd_ratio(self,
                           rd_expense: float,
                           revenue: float) -> float:
        """
        计算研发费用占比
        
        Args:
            rd_expense: 研发费用
            revenue: 营收
            
        Returns:
            研发占比
        """
        if revenue <= 0:
            return np.nan
        
        return rd_expense / revenue
    
    # ==================== 估值因子计算 ====================
    
    def calculate_pe(self,
                      price: float,
                      earnings: float) -> float:
        """
        计算PE
        
        Args:
            price: 价格
            earnings: 每股收益
            
        Returns:
            PE
        """
        if earnings <= 0:
            return np.nan
        
        return price / earnings
    
    def calculate_pe_percentile(self,
                                current_pe: float,
                                historical_pe: List[float]) -> float:
        """
        计算PE历史分位
        
        Args:
            current_pe: 当前PE
            historical_pe: 历史PE列表
            
        Returns:
            PE分位 (0-100)
        """
        if len(historical_pe) == 0:
            return np.nan
        
        pe_array = np.array(historical_pe)
        percentile = (current_pe < pe_array).sum() / len(pe_array) * 100
        
        return percentile
    
    def calculate_peg(self,
                       pe: float,
                       growth_rate: float) -> float:
        """
        计算PEG
        
        PEG = PE / (增长率 * 100)
        
        Args:
            pe: PE
            growth_rate: 增长率 (如0.25表示25%)
            
        Returns:
            PEG
        """
        if growth_rate <= 0:
            return np.nan
        
        return pe / (growth_rate * 100)
    
    def calculate_pb(self,
                      price: float,
                      book_value: float) -> float:
        """
        计算PB
        
        Args:
            price: 价格
            book_value: 每股净资产
            
        Returns:
            PB
        """
        if book_value <= 0:
            return np.nan
        
        return price / book_value
    
    # ==================== 资金流向因子计算 ====================
    
    def calculate_capital_flow(self,
                                close_prices: pd.Series,
                                volumes: pd.Series,
                                large_order_threshold: float = 0.1) -> pd.DataFrame:
        """
        计算资金流向
        
        Args:
            close_prices: 收盘价序列
            volumes: 成交量序列
            large_order_threshold: 大单阈值（成交额占比）
            
        Returns:
            资金流向DataFrame
        """
        # 计算成交额
        turnover = close_prices * volumes
        
        # 计算价格变化
        price_change = close_prices.pct_change()
        
        # 简化的大单资金流向计算
        flow = pd.DataFrame(index=close_prices.index)
        flow['net_flow'] = price_change * volumes
        flow['net_flow_rate'] = flow['net_flow'] / turnover
        
        return flow
    
    def calculate_margin_balance_change(self,
                                          margin_balance: pd.Series,
                                          window: int = 10) -> pd.Series:
        """
        计算融资余额变化
        
        Args:
            margin_balance: 融资余额序列
            window: 计算窗口期
            
        Returns:
            融资余额变化率
        """
        margin_change = margin_balance.pct_change(window)
        
        return margin_change
    
    # ==================== 换手率因子计算 ====================
    
    def calculate_turnover(self,
                           volumes: pd.Series,
                           outstanding_shares: pd.Series) -> pd.Series:
        """
        计算换手率
        
        Args:
            volumes: 成交量序列
            outstanding_shares: 流通股数序列
            
        Returns:
            换手率序列
        """
        turnover = volumes / outstanding_shares
        turnover = turnover.replace([np.inf, -np.inf], np.nan)
        
        return turnover
    
    def calculate_turnover_change(self,
                                   turnover: pd.Series,
                                   current: float,
                                   average_window: int = 20) -> float:
        """
        计算换手率变化
        
        Args:
            turnover: 换手率序列
            current: 当前换手率
            average_window: 平均窗口期
            
        Returns:
            换手率变化倍数
        """
        avg_turnover = turnover.tail(average_window).mean()
        
        if avg_turnover <= 0:
            return np.nan
        
        return current / avg_turnover
    
    # ==================== 综合因子计算 ====================
    
    def normalize_factor(self,
                          factor: pd.Series,
                          method: str = 'zscore') -> pd.Series:
        """
        因子标准化
        
        Args:
            factor: 因子值序列
            method: 标准化方法 ('zscore', 'rank', 'minmax')
            
        Returns:
            标准化后的因子值
        """
        if method == 'zscore':
            # Z-score标准化
            mean = factor.mean()
            std = factor.std()
            
            if std == 0:
                return pd.Series(0, index=factor.index)
            
            return (factor - mean) / std
        
        elif method == 'rank':
            # 排名百分位
            return factor.rank(pct=True)
        
        elif method == 'minmax':
            # Min-Max标准化
            min_val = factor.min()
            max_val = factor.max()
            
            if max_val == min_val:
                return pd.Series(0.5, index=factor.index)
            
            return (factor - min_val) / (max_val - min_val)
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def calculate_composite_factor(self,
                                    factors: Dict[str, pd.Series],
                                    weights: Dict[str, float]) -> pd.Series:
        """
        计算综合因子
        
        Args:
            factors: 因子字典
            weights: 权重字典
            
        Returns:
            综合因子得分
        """
        normalized_factors = {}
        
        for name, factor in factors.items():
            if name in weights:
                normalized_factors[name] = self.normalize_factor(factor)
        
        # 加权求和
        composite = pd.Series(0, index=factor.index)
        
        for name, weight in weights.items():
            if name in normalized_factors:
                composite += normalized_factors[name] * weight
        
        return composite
    
    # ==================== 成交量因子计算 ====================
    
    def calculate_volume_ratio(self,
                                volumes: pd.Series,
                                window: int = 20) -> pd.Series:
        """
        量比
        
        Args:
            volumes: 成交量序列
            window: 计算窗口期
            
        Returns:
            量比序列
        """
        avg_volume = volumes.rolling(window=window).mean()
        
        vr = volumes / avg_volume
        vr = vr.replace([np.inf, -np.inf], np.nan)
        
        return vr
    
    def calculate_volume_price_trend(self,
                                      prices: pd.Series,
                                      volumes: pd.Series) -> pd.Series:
        """
        量价趋势
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            
        Returns:
            量价趋势得分
        """
        price_change = prices.pct_change()
        volume_change = volumes.pct_change()
        
        # 计算相关系数
        vpt = price_change * volume_change
        
        return vpt
    
    def calculate_updown_ratio(self,
                               涨停数量: pd.Series,
                                跌停数量: pd.Series) -> pd.Series:
        """
        涨跌停比
        
        Args:
            涨停数量: 涨停股票数序列
            跌停数量: 跌停股票数序列
            
        Returns:
            涨跌停比序列
        """
        ratio = 涨停数量 / (跌停数量 + 1)
        
        return ratio
