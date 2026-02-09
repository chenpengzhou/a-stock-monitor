"""
牛市高倍收益策略 - 示例运行脚本
================================

展示如何使用四大核心策略模块进行回测。

Author: OpenClaw
Date: 2026-02-09
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from . import (
    HighBetaStrategy,
    TrendFollowingStrategy,
    SectorRotationStrategy,
    GrowthStockStrategy,
    MarketStageDetector,
    RiskManager,
    BacktestEngine,
    FactorCalculator,
    StrategyConfig
)


def generate_sample_data(start_date: str, end_date: str, n_stocks: int = 50) -> tuple:
    """
    生成示例数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        n_stocks: 股票数量
        
    Returns:
        (市场数据, 基准数据)
    """
    # 生成日期
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # 生成股票代码
    stocks = [f'STOCK_{i:03d}' for i in range(1, n_stocks + 1)]
    
    # 生成市场数据
    market_data = []
    
    for stock in stocks:
        # 随机参数
        base_return = np.random.uniform(0.0005, 0.002)
        volatility = np.random.uniform(0.02, 0.04)
        
        # 生成价格序列
        returns = np.random.normal(base_return, volatility, len(dates))
        prices = 100 * (1 + returns).cumprod()
        
        # 生成成交量
        volumes = np.random.randint(1000000, 10000000, len(dates))
        
        # 生成财务数据（简化）
        market_cap = np.random.uniform(100, 2000, len(dates))
        roe = np.random.uniform(0.08, 0.25)
        
        for i, date in enumerate(dates):
            market_data.append({
                'date': date,
                'symbol': stock,
                'close': prices[i],
                'volume': volumes[i],
                'market_cap': market_cap[i],
                'roe': roe,
                'sector': np.random.choice(['金融', 'TMT', '消费', '周期', '医药'])
            })
    
    market_df = pd.DataFrame(market_data)
    market_df.set_index(['date', 'symbol'], inplace=True)
    
    # 生成基准数据 (沪深300)
    benchmark_returns = pd.Series(
        np.random.normal(0.0008, 0.015, len(dates)),
        index=dates,
        name='benchmark'
    )
    benchmark_data = (1 + benchmark_returns).cumprod() * 1000
    
    return market_df, benchmark_data


def demo_high_beta_strategy():
    """演示高Beta策略"""
    print("\n" + "="*60)
    print("高Beta策略演示")
    print("="*60)
    
    config = StrategyConfig()
    strategy = HighBetaStrategy(config.high_beta.__dict__)
    
    # 生成示例数据
    market_data, benchmark = generate_sample_data('20230101', '20231231', 30)
    benchmark_returns = benchmark.pct_change()
    
    # 运行回测
    result = strategy.run_backtest(market_data, benchmark_returns, initial_capital=1000000)
    
    print(f"选股数量: {result['position_count']}")
    print(f"平均Beta: {result['avg_beta']:.2f}")
    print(f"模拟收益: {(result['final_capital']/1000000-1)*100:.2f}%")
    
    return result


def demo_trend_strategy():
    """演示趋势追踪策略"""
    print("\n" + "="*60)
    print("趋势追踪策略演示")
    print("="*60)
    
    config = StrategyConfig()
    strategy = TrendFollowingStrategy(config.trend.__dict__)
    
    # 生成示例数据
    market_data, benchmark = generate_sample_data('20230101', '20231231', 20)
    benchmark_returns = benchmark.pct_change()
    
    # 运行回测
    result = strategy.run_backtest(market_data, benchmark_returns, initial_capital=1000000)
    
    print(f"趋势信号数量: {len(result['signals'])}")
    print(f"当前持仓: {result['position_count']}")
    print(f"模拟收益: {(result['final_capital']/1000000-1)*100:.2f}%")
    
    return result


def demo_sector_rotation_strategy():
    """演示板块轮动策略"""
    print("\n" + "="*60)
    print("板块轮动策略演示")
    print("="*60)
    
    config = StrategyConfig()
    strategy = SectorRotationStrategy(config.sector_rotation.__dict__)
    
    # 生成板块数据
    sectors = ['券商', '银行', '电子', '计算机', '医药', '食品饮料', '新能源', '军工']
    
    sector_data = pd.DataFrame({
        '券商': 100 * (1 + np.random.normal(0.001, 0.025, 252)).cumprod(),
        '银行': 100 * (1 + np.random.normal(0.0008, 0.02, 252)).cumprod(),
        '电子': 100 * (1 + np.random.normal(0.0012, 0.03, 252)).cumprod(),
        '计算机': 100 * (1 + np.random.normal(0.001, 0.035, 252)).cumprod(),
        '医药': 100 * (1 + np.random.normal(0.0009, 0.025, 252)).cumprod(),
        '食品饮料': 100 * (1 + np.random.normal(0.0008, 0.02, 252)).cumprod(),
        '新能源': 100 * (1 + np.random.normal(0.0015, 0.035, 252)).cumprod(),
        '军工': 100 * (1 + np.random.normal(0.001, 0.028, 252)).cumprod(),
    }, index=pd.date_range('20230101', periods=252, freq='B'))
    
    benchmark_returns = sector_data.mean(axis=1).pct_change()
    
    # 运行回测
    result = strategy.run_backtest(sector_data, benchmark_returns, initial_capital=1000000)
    
    print(f"主线板块: {result['main_sectors']}")
    print(f"板块数量: {result['position_count']}")
    print(f"模拟收益: {(result['final_capital']/1000000-1)*100:.2f}%")
    
    return result


def demo_growth_strategy():
    """演示成长股精选策略"""
    print("\n" + "="*60)
    print("成长股精选策略演示")
    print("="*60)
    
    config = StrategyConfig()
    strategy = GrowthStockStrategy(config.growth.__dict__)
    
    # 生成示例数据
    market_data, benchmark = generate_sample_data('20230101', '20231231', 30)
    
    # 生成财务数据
    fundamental_data = []
    for stock in market_data.index.get_level_values('symbol').unique():
        fundamental_data.append({
            'symbol': stock,
            'revenue': [100 + np.random.randint(10, 50) * i for i in range(8)],
            'net_profit': [10 + np.random.randint(2, 10) * i for i in range(8)],
            'roe': np.random.uniform(0.15, 0.30),
            'gross_margin': np.random.uniform(0.30, 0.50),
            'operating_cash_flow': np.random.uniform(8, 15),
            'rd_expense': np.random.uniform(5, 20),
            'eps': np.random.uniform(0.5, 2.0),
            'actual_earnings': [1.0 + np.random.uniform(-0.1, 0.2) for _ in range(8)],
            'expected_earnings': [1.0 for _ in range(8)]
        })
    
    fund_df = pd.DataFrame(fundamental_data)
    fund_df.set_index('symbol', inplace=True)
    
    # 生成板块数据
    sector_data = pd.DataFrame({
        'symbol': fundamental_data[0]['symbol'],
        'sector': np.random.choice(['TMT', '医药', '消费'])
    }, index=[f'STOCK_{i:03d}' for i in range(1, 31)])
    
    # 运行回测
    result = strategy.run_backtest(fund_df, market_data, sector_data, initial_capital=1000000)
    
    print(f"初筛数量: {result['candidates_count']}")
    print(f"深度研究: {result['deep_candidates_count']}")
    print(f"组合数量: {result['portfolio_size']}")
    print(f"模拟收益: {(result['final_capital']/1000000-1)*100:.2f}%")
    
    return result


def demo_market_stage_detection():
    """演示市场阶段检测"""
    print("\n" + "="*60)
    print("市场阶段检测演示")
    print("="*60)
    
    detector = MarketStageDetector()
    
    # 生成示例数据
    dates = pd.date_range('20230101', periods=252, freq='B')
    
    # 模拟牛市数据
    prices = 100 * (1 + np.random.normal(0.001, 0.015, 252)).cumprod()
    volumes = np.random.randint(5000000, 15000000, 252)
    
    market_df = pd.DataFrame({
        'close': prices,
        'volume': volumes
    }, index=dates)
    
    # 检测市场阶段
    stage, indicators = detector.detect_market_stage(market_df)
    
    print(f"检测到的市场阶段: {stage.value}")
    print(f"阶段描述: {detector.get_stage_description(stage)}")
    print(f"置信度: {indicators.overall_score:.1f}%")
    print(f"20日动量: {indicators.momentum_20d:.2%}")
    print(f"量比: {indicators.volume_ratio:.2f}")
    print(f"均线状态: {indicators.ma_status}")
    
    # 获取对应配置
    config = detector.get_stage_position_config(stage)
    print(f"\n建议仓位: {config['position']:.0%}")
    print(f"目标Beta: {config['beta_target']:.1f}")
    print(f"关注板块: {config['focus']}")
    
    return stage, indicators


def demo_risk_management():
    """演示风险管理"""
    print("\n" + "="*60)
    print("风险管理演示")
    print("="*60)
    
    manager = RiskManager()
    
    # 示例持仓
    positions = {
        'STOCK_001': {'weight': 0.08, 'sector': 'TMT'},
        'STOCK_002': {'weight': 0.06, 'sector': '金融'},
        'STOCK_003': {'weight': 0.07, 'sector': 'TMT'},
        'STOCK_004': {'weight': 0.05, 'sector': '消费'},
        'STOCK_005': {'weight': 0.04, 'sector': '医药'}
    }
    
    sectors = {
        'TMT': ['STOCK_001', 'STOCK_003'],
        '金融': ['STOCK_002'],
        '消费': ['STOCK_004'],
        '医药': ['STOCK_005']
    }
    
    daily_turnover = {
        'STOCK_001': 8.5,
        'STOCK_002': 12.0,
        'STOCK_003': 5.2,
        'STOCK_004': 6.8,
        'STOCK_005': 4.5
    }
    
    # 事前风控检查
    passed, alerts = manager.before_trade(positions, sectors, daily_turnover)
    
    print(f"风控检查通过: {'是' if passed else '否'}")
    print(f"预警数量: {len(alerts)}")
    
    for alert in alerts[:5]:
        print(f"  - [{alert.severity}] {alert.message}")
    
    # 计算风险指标
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, 252))
    
    metrics = manager.calculate_risk_metrics(returns, benchmark_returns)
    
    print(f"\n风险指标:")
    print(f"  年化收益: {metrics.annualized_return:.2%}")
    print(f"  波动率: {metrics.volatility:.2%}")
    print(f"  最大回撤: {metrics.max_drawdown:.2%}")
    print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"  风险等级: {metrics.risk_level.value}")
    
    return manager, metrics


def demo_full_backtest():
    """演示完整回测流程"""
    print("\n" + "="*60)
    print("完整回测流程演示")
    print("="*60)
    
    # 创建回测引擎
    engine = BacktestEngine()
    
    # 生成示例数据
    market_data, benchmark = generate_sample_data('20230101', '20231231', 50)
    engine.load_data(market_data, benchmark)
    
    # 运行回测
    metrics, daily_records, trades = engine.run_backtest()
    
    # 生成报告
    report = engine.generate_report(metrics, daily_records, trades)
    
    print("\n回测结果摘要:")
    print(f"  总收益: {report['summary']['total_return']}")
    print(f"  年化收益: {report['summary']['annualized_return']}")
    print(f"  波动率: {report['summary']['volatility']}")
    print(f"  最大回撤: {report['summary']['max_drawdown']}")
    print(f"  夏普比率: {report['summary']['sharpe_ratio']}")
    print(f"  胜率: {report['summary']['win_rate']}")
    print(f"  总交易次数: {report['summary']['total_trades']}")
    
    return metrics, daily_records, trades


def main():
    """主函数"""
    print("="*60)
    print("牛市高倍收益策略 - 演示程序")
    print("="*60)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 高Beta策略演示
    demo_high_beta_strategy()
    
    # 2. 趋势追踪策略演示
    demo_trend_strategy()
    
    # 3. 板块轮动策略演示
    demo_sector_rotation_strategy()
    
    # 4. 成长股精选策略演示
    demo_growth_strategy()
    
    # 5. 市场阶段检测演示
    demo_market_stage_detection()
    
    # 6. 风险管理演示
    demo_risk_management()
    
    # 7. 完整回测演示
    demo_full_backtest()
    
    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)


if __name__ == '__main__':
    main()
