"""
低波动率策略 - 自测验证
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import sys
import os
# 添加父目录（让 lowvol_strategy 成为包）
pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

# 现在可以正确导入子模块
from lowvol_strategy.config.lowvol_config import LowVolConfig
from lowvol_strategy.factors import (
    VolatilityFactor,
    ATRFactor,
    BetaFactor,
    QualityFactor,
    CompositeLowVolScore
)
from lowvol_strategy.selection import LowVolStockSelector
from lowvol_strategy.position import PositionManager
from lowvol_strategy.backtest.performance import PerformanceAnalyzer
from lowvol_strategy.backtest.backtest_engine import LowVolBacktest


class SelfTest:
    """
    策略自测类
    """
    
    def __init__(self):
        self.config = LowVolConfig()
        self.test_results = []
    
    def _record_test(self, name: str, passed: bool, details: str = ""):
        self.test_results.append({
            'name': name,
            'passed': passed,
            'details': details
        })
    
    def test_volatility_factor(self) -> bool:
        try:
            factor = VolatilityFactor(window=20)
            np.random.seed(42)
            prices = pd.Series(100 * (1 + np.random.randn(100) * 0.02))
            vol = factor.calculate(prices)
            
            assert isinstance(vol, float), "返回值类型错误"
            assert 0 <= vol <= 100, "波动率范围异常"
            
            self._record_test("波动率因子计算", True, f"成功计算波动率: {vol:.2f}%")
            return True
        except Exception as e:
            self._record_test("波动率因子计算", False, f"计算失败: {str(e)}")
            return False
    
    def test_atr_factor(self) -> bool:
        try:
            factor = ATRFactor(window=14)
            np.random.seed(42)
            n = 100
            close = 100 * (1 + np.cumsum(np.random.randn(n) * 0.02))
            high = close + np.abs(np.random.randn(n) * 2)
            low = close - np.abs(np.random.randn(n) * 2)
            atr_percent = factor.calculate_atr_percent(high, low, close)
            
            assert isinstance(atr_percent, pd.Series), "返回值类型错误"
            assert len(atr_percent) == n, "长度不匹配"
            
            self._record_test("ATR因子计算", True, f"成功计算ATR百分比，均值: {atr_percent.mean():.2f}%")
            return True
        except Exception as e:
            self._record_test("ATR因子计算", False, f"计算失败: {str(e)}")
            return False
    
    def test_beta_factor(self) -> bool:
        try:
            factor = BetaFactor(window=60)
            np.random.seed(42)
            n = 200
            market_returns = np.random.randn(n) * 0.01
            stock_returns = market_returns * 1.2 + np.random.randn(n) * 0.005
            beta = factor.calculate_beta(stock_returns, market_returns)
            
            assert isinstance(beta, pd.Series), "返回值类型错误"
            
            self._record_test("Beta因子计算", True, f"成功计算Beta，最新值: {beta.iloc[-1]:.2f}")
            return True
        except Exception as e:
            self._record_test("Beta因子计算", False, f"计算失败: {str(e)}")
            return False
    
    def test_quality_factor(self) -> bool:
        try:
            factor = QualityFactor()
            np.random.seed(42)
            n = 100
            roe = pd.Series(np.random.uniform(5, 20, n))
            debt_ratio = pd.Series(np.random.uniform(30, 80, n))
            dividend = pd.Series(np.random.uniform(0.3, 3, n))
            quality_score = factor.calculate_composite_quality_score(roe, debt_ratio, dividend)
            
            assert isinstance(quality_score, pd.Series), "返回值类型错误"
            assert len(quality_score) == n, "长度不匹配"
            
            self._record_test("质量因子计算", True, f"成功计算质量得分，均值: {quality_score.mean():.2f}")
            return True
        except Exception as e:
            self._record_test("质量因子计算", False, f"计算失败: {str(e)}")
            return False
    
    def test_composite_score(self) -> bool:
        try:
            scorer = CompositeLowVolScore()
            np.random.seed(42)
            n = 50
            volatility = pd.Series(np.random.uniform(15, 40, n))
            atr_percent = pd.Series(np.random.uniform(2, 8, n))
            beta = pd.Series(np.random.uniform(0.5, 1.5, n))
            quality = pd.Series(np.random.uniform(0.3, 0.8, n))
            composite = scorer.calculate(volatility, atr_percent, beta, quality)
            
            assert isinstance(composite, pd.Series), "返回值类型错误"
            assert len(composite) == n, "长度不匹配"
            
            self._record_test("复合低波评分", True, f"成功计算复合评分，均值: {composite.mean():.2f}")
            return True
        except Exception as e:
            self._record_test("复合低波评分", False, f"计算失败: {str(e)}")
            return False
    
    def test_stock_selector(self) -> bool:
        try:
            selector = LowVolStockSelector(self.config)
            
            np.random.seed(42)
            n = 100
            codes = [f'STOCK_{i:04d}' for i in range(n)]
            
            data = pd.DataFrame({
                'code': codes,
                'listing_days': np.random.randint(180, 5000, n),
                'avg_turnover': np.random.uniform(1000, 10000, n),
                'roe': np.random.uniform(3, 25, n),
                'debt_ratio': np.random.uniform(20, 90, n),
                'dividend_yield': np.random.uniform(0.1, 4, n),
                'volatility': np.random.uniform(15, 50, n),
                'beta': np.random.uniform(0.3, 2.0, n),
                'atr_percent': np.random.uniform(1, 10, n),
                'quality_score': np.random.uniform(0.2, 0.9, n),
                'industry': np.random.choice(['银行', '医药', '消费', '科技', '制造'], n)
            })
            
            selected, details = selector.select(data, return_details=True)
            
            assert isinstance(selected, pd.Series), "返回值类型错误"
            assert isinstance(details, pd.DataFrame), "返回值类型错误"
            
            num_selected = selected.sum()
            
            self._record_test("选股器功能", True, f"成功选股，候选: {n}只，选中: {int(num_selected)}只")
            return True
        except Exception as e:
            self._record_test("选股器功能", False, f"选股失败: {str(e)}")
            return False
    
    def test_position_manager(self) -> bool:
        try:
            manager = PositionManager(self.config)
            
            stocks = [f'STOCK_{i:04d}' for i in range(30)]
            weights = manager.calculate_equal_weight(stocks)
            
            assert len(weights) == 30, "权重数量不匹配"
            assert abs(sum(weights.values()) - 1.0) < 1e-6, "权重之和不为1"
            
            for w in weights.values():
                assert w <= self.config.MAX_SINGLE_WEIGHT, "单只权重超限"
            
            stock_industry = {s: f'Industry_{i % 5}' for i, s in enumerate(stocks)}
            controlled = manager.apply_risk_controls(weights, stock_industry)
            
            industry_weights = {}
            for stock, weight in controlled.items():
                industry = stock_industry[stock]
                industry_weights[industry] = industry_weights.get(industry, 0) + weight
            
            for ind_w in industry_weights.values():
                assert ind_w <= self.config.MAX_INDUSTRY_WEIGHT, "行业权重超限"
            
            self._record_test("仓位管理器", True, f"成功计算仓位")
            return True
        except Exception as e:
            self._record_test("仓位管理器", False, f"仓位计算失败: {str(e)}")
            return False
    
    def test_backtest_engine(self) -> bool:
        try:
            from backtest.backtest_engine import LowVolBacktest
            backtest = LowVolBacktest(self.config)
            
            np.random.seed(42)
            n_stocks = 50
            n_days = 500
            start_date = datetime(2020, 1, 1)
            
            stock_codes = [f'STOCK_{i:04d}' for i in range(n_stocks)]
            dates = [start_date + timedelta(days=i) for i in range(n_days)]
            
            data_rows = []
            for stock in stock_codes:
                base_price = np.random.uniform(10, 100)
                volatility = np.random.uniform(15, 40)
                beta = np.random.uniform(0.5, 1.5)
                
                for i, date in enumerate(dates):
                    daily_return = np.random.randn() * 0.02
                    close = base_price * (1 + daily_return)
                    high = close * (1 + np.abs(np.random.randn()) * 0.02)
                    low = close * (1 - np.abs(np.random.randn()) * 0.02)
                    
                    data_rows.append({
                        'code': stock,
                        'date': date,
                        'close': close,
                        'high': high,
                        'low': low,
                        'volatility': volatility + np.random.randn() * 2,
                        'beta': beta + np.random.randn() * 0.1,
                        'atr_percent': np.random.uniform(2, 8),
                        'roe': np.random.uniform(5, 20),
                        'debt_ratio': np.random.uniform(30, 70),
                        'dividend_yield': np.random.uniform(0.5, 3),
                        'quality_score': np.random.uniform(0.3, 0.8),
                        'industry': np.random.choice(['银行', '医药', '消费', '科技', '制造']),
                        'listing_days': np.random.randint(500, 5000),
                        'avg_turnover': np.random.uniform(3000, 10000)
                    })
            
            data = pd.DataFrame(data_rows)
            
            backtest.load_data(data)
            results = backtest.run()
            
            assert '年化收益率' in results, "结果缺少年化收益率"
            assert '最大回撤' in results, "结果缺少最大回撤"
            assert '夏普比率' in results, "结果缺少夏普比率"
            
            self._record_test("回测引擎", True, f"成功运行回测，年化收益: {results['年化收益率']:.2f}%, 最大回撤: {results['最大回撤']:.2f}%")
            return True
        except Exception as e:
            self._record_test("回测引擎", False, f"回测失败: {str(e)}")
            return False
    
    def test_performance_analyzer(self) -> bool:
        try:
            from backtest.performance import PerformanceAnalyzer
            analyzer = PerformanceAnalyzer()
            
            np.random.seed(42)
            n_days = 252
            start_value = 1000000
            
            portfolio_history = []
            current_value = start_value
            
            for i in range(n_days):
                daily_return = np.random.randn() * 0.01
                current_value *= (1 + daily_return)
                
                portfolio_history.append({
                    'date': datetime(2020, 1, 1) + timedelta(days=i),
                    'portfolio_value': current_value,
                    'cash': current_value * 0.1,
                    'positions_value': current_value * 0.9
                })
            
            results = analyzer.analyze(portfolio_history)
            
            assert '年化收益率' in results, "结果缺少年化收益率"
            assert '年化波动率' in results, "结果缺少年化波动率"
            assert '最大回撤' in results, "结果缺少最大回撤"
            
            self._record_test("绩效分析器", True, f"成功分析绩效，年化收益: {results['年化收益率']:.2f}%")
            return True
        except Exception as e:
            self._record_test("绩效分析器", False, f"绩效分析失败: {str(e)}")
            return False
    
    def run_all_tests(self) -> List[Dict]:
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("低波动率策略 - 自测验证")
        print("=" * 60 + "\n")
        
        self.test_results = []
        
        tests = [
            ("波动率因子", self.test_volatility_factor),
            ("ATR因子", self.test_atr_factor),
            ("Beta因子", self.test_beta_factor),
            ("质量因子", self.test_quality_factor),
            ("复合评分", self.test_composite_score),
            ("选股器", self.test_stock_selector),
            ("仓位管理", self.test_position_manager),
            ("回测引擎", self.test_backtest_engine),
            ("绩效分析", self.test_performance_analyzer),
        ]
        
        for name, test_func in tests:
            print(f"测试 {name}...", end=" ")
            passed = test_func()
            if passed:
                print("✓")
            else:
                print("✗")
        
        return self.test_results
    
    def print_results(self, results: List[Dict] = None):
        """打印测试结果"""
        if results is None:
            results = self.test_results
        
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"\n通过: {passed_count}/{total_count}")
        
        for r in results:
            status = "✓" if r['passed'] else "✗"
            print(f"\n[{status}] {r['name']}")
            if r['details']:
                print(f"    {r['details']}")
        
        print("\n" + "=" * 60)
        
        if passed_count == total_count:
            print("✓ 所有测试通过！")
        else:
            print(f"✗ {total_count - passed_count} 个测试未通过")
        
        print("=" * 60 + "\n")
