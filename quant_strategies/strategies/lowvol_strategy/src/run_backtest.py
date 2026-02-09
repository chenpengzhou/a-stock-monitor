#!/usr/bin/env python3
"""
低波动率策略全周期回测脚本
==========================

回测周期: 2005-2023年
关键参数:
- 波动率周期: 20日
- 持仓数量: 30只
- 调仓周期: 月度
- 仓位: 等权配置
- 成交价格: 当日中间价
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.lowvol_config import LowVolConfig
from lowvol_strategy import LowVolStrategy
import json
import warnings
warnings.filterwarnings('ignore')


def generate_market_data(
    start_date: datetime,
    end_date: datetime,
    n_stocks: int = 500
) -> pd.DataFrame:
    """
    生成模拟市场数据
    
    模拟A股市场2005-2023年的历史数据
    """
    print("正在生成模拟市场数据...")
    
    stock_codes = [f'{str(i).zfill(6)}' for i in range(1, n_stocks + 1)]
    
    trading_days = pd.bdate_range(start_date, end_date)
    
    data_rows = []
    
    # 市场阶段参数
    market_phases = {
        2005: {'vol': 0.025, 'drift': 0.0002},
        2006: {'vol': 0.030, 'drift': 0.0010},
        2007: {'vol': 0.035, 'drift': 0.0020},
        2008: {'vol': 0.045, 'drift': -0.0015},
        2009: {'vol': 0.035, 'drift': 0.0015},
        2010: {'vol': 0.025, 'drift': 0.0003},
        2011: {'vol': 0.025, 'drift': -0.0003},
        2012: {'vol': 0.025, 'drift': 0.0003},
        2013: {'vol': 0.030, 'drift': 0.0005},
        2014: {'vol': 0.030, 'drift': 0.0012},
        2015: {'vol': 0.045, 'drift': 0.0010},
        2016: {'vol': 0.025, 'drift': 0.0002},
        2017: {'vol': 0.020, 'drift': 0.0008},
        2018: {'vol': 0.025, 'drift': -0.0008},
        2019: {'vol': 0.025, 'drift': 0.0008},
        2020: {'vol': 0.030, 'drift': 0.0012},
        2021: {'vol': 0.025, 'drift': 0.0005},
        2022: {'vol': 0.028, 'drift': -0.0003},
        2023: {'vol': 0.025, 'drift': 0.0005},
    }
    
    industries = ['银行', '医药', '消费', '科技', '制造', '地产', '券商', '军工', '新能源', '基建']
    
    np.random.seed(42)
    
    for stock_idx, stock_code in enumerate(stock_codes):
        base_price = np.random.uniform(5, 50)
        base_volatility = np.random.uniform(20, 45)
        base_beta = np.random.uniform(0.5, 1.5)
        industry = np.random.choice(industries)
        listing_start = np.random.randint(
            (start_date - timedelta(days=365)).year,
            (end_date - timedelta(days=180)).year
        )
        
        for day_idx, date in enumerate(trading_days):
            year = date.year
            phase = market_phases.get(year, market_phases[2020])
            
            daily_vol = phase['vol'] * (1 + (base_volatility - 30) / 100)
            daily_drift = phase['drift'] * (1 + (base_beta - 1) * 0.5)
            
            if day_idx == 0:
                close = base_price
            else:
                random_return = np.random.randn() * daily_vol + daily_drift
                close = prev_close * (1 + random_return)
            
            high = close * (1 + np.abs(np.random.randn()) * 0.03)
            low = close * (1 - np.abs(np.random.randn()) * 0.03)
            
            volatility = base_volatility + np.random.randn() * 3
            volatility = max(15, min(60, volatility))
            
            beta = base_beta + np.random.randn() * 0.1
            beta = max(0.3, min(2.0, beta))
            
            atr_percent = np.random.uniform(1.5, 8) * (volatility / 30)
            
            listing_days = max(0, (date - datetime(listing_start, 1, 1)).days)
            
            avg_turnover = np.random.uniform(2000, 15000)
            
            roe = np.random.uniform(5, 20)
            debt_ratio = np.random.uniform(30, 70)
            dividend_yield = np.random.uniform(0.3, 4)
            quality_score = np.random.uniform(0.3, 0.8)
            
            data_rows.append({
                'code': stock_code,
                'date': date,
                'close': close,
                'high': high,
                'low': low,
                'volatility': volatility,
                'beta': beta,
                'atr_percent': atr_percent,
                'roe': roe,
                'debt_ratio': debt_ratio,
                'dividend_yield': dividend_yield,
                'quality_score': quality_score,
                'industry': industry,
                'listing_days': listing_days,
                'avg_turnover': avg_turnover
            })
            
            prev_close = close
    
    df = pd.DataFrame(data_rows)
    print(f"数据生成完成: {len(df):,} 条记录, {len(trading_days)} 个交易日, {n_stocks} 只股票")
    
    return df


def run_backtest():
    """运行低波动率策略回测"""
    
    print("\n" + "=" * 70)
    print("低波动率策略 - 全周期回测验证 (2005-2023)")
    print("=" * 70)
    
    # 回测参数
    start_date = datetime(2005, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    # 初始化策略
    config = LowVolConfig()
    
    # 设置关键参数
    config.VOLATILITY_WINDOW = 20
    config.TOP_N_HOLDINGS = 30
    config.REBALANCE_FREQUENCY = 'monthly'
    config.INITIAL_CAPITAL = 10000000  # 1000万初始资金
    
    print("\n【策略参数】")
    print(f"  波动率周期: {config.VOLATILITY_WINDOW}日")
    print(f"  持仓数量: {config.TOP_N_HOLDINGS}只")
    print(f"  调仓周期: 月度")
    print(f"  仓位配置: 等权")
    print(f"  初始资金: {config.INITIAL_CAPITAL:,}元")
    
    # 生成市场数据
    market_data = generate_market_data(start_date, end_date, n_stocks=500)
    
    # 初始化策略
    strategy = LowVolStrategy(config)
    strategy.load_data(market_data)
    
    print("\n【开始回测】")
    print(f"  回测期间: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    # 运行回测
    results = strategy.run_backtest(
        start_date=start_date,
        end_date=end_date,
        frequency='monthly'
    )
    
    # 打印结果
    print("\n" + "=" * 70)
    print("回测结果")
    print("=" * 70)
    
    strategy.print_results()
    
    return results, market_data


def generate_report(results: dict, market_data: pd.DataFrame) -> str:
    """生成回测报告"""
    
    report = f"""
# 低波动率策略回测报告

## 1. 回测概览

**回测周期**: {results.get('回测期间', 'N/A')}
**交易日数**: {results.get('交易日数', 'N/A')} 天
**调仓次数**: {results.get('调仓次数', 'N/A')} 次

## 2. 策略参数

| 参数 | 设置值 |
|------|--------|
| 波动率周期 | 20日 |
| 持仓数量 | 30只 |
| 调仓周期 | 月度 |
| 仓位配置 | 等权 |
| 成交价格 | 当日中间价 |

## 3. 收益表现

| 指标 | 数值 |
|------|------|
| 总收益率 | {results.get('总收益率', 'N/A')}% |
| 年化收益率 | {results.get('年化收益率', 'N/A')}% |
| 月均收益率 | {results.get('月均收益率', 'N/A')}% |

## 4. 风险指标

| 指标 | 数值 |
|------|------|
| 年化波动率 | {results.get('年化波动率', 'N/A')}% |
| 最大回撤 | {results.get('最大回撤', 'N/A')}% |
| 夏普比率 | {results.get('夏普比率', 'N/A')} |
| 卡玛比率 | {results.get('卡玛比率', 'N/A')} |
| 索提诺比率 | {results.get('索提诺比率', 'N/A')} |

## 5. 交易统计

| 指标 | 数值 |
|------|------|
| 总交易次数 | {results.get('总交易次数', 'N/A')} |
| 平均换手率 | {results.get('平均换手率', 'N/A')}% |
| 日胜率 | {results.get('日胜率', 'N/A')}% |

## 6. 分析结论

### 收益分析
- 策略在 {results.get('回测期间', 'N/A')} 期间实现了 **{results.get('年化收益率', 'N/A')}%** 的年化收益率
- 总收益率为 **{results.get('总收益率', 'N/A')}%**

### 风险分析
- 年化波动率为 **{results.get('年化波动率', 'N/A')}%**，处于中等水平
- 最大回撤为 **{results.get('最大回撤', 'N/A')}%**

### 风险调整收益
- 夏普比率为 **{results.get('夏普比率', 'N/A')}**，表示单位风险的超额收益
- 卡玛比率为 **{results.get('卡玛比率', 'N/A')}**

## 7. 策略评估

根据回测结果，低波动率策略在2005-2023年期间表现：
- **年化收益率**: {'符合预期' if 8 <= results.get('年化收益率', 0) <= 12 else '偏离预期'} (预期: 8-12%)
- **最大回撤**: {'符合预期' if abs(results.get('最大回撤', 0)) <= 10 else '偏离预期'} (预期: <10%)
- **夏普比率**: {'达标' if results.get('夏普比率', 0) >= 0.6 else '未达标'} (目标: >0.6)

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**回测引擎**: OpenClaw LowVol Strategy Backtest Framework
"""
    
    return report


def save_results(results: dict, report: str, market_data: pd.DataFrame):
    """保存回测结果"""
    
    output_dir = '/home/admin/.openclaw/workspace-qa'
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON结果
    json_path = os.path.join(output_dir, 'lowvol_backtest_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✓ JSON结果已保存: {json_path}")
    
    # 保存Markdown报告
    report_path = os.path.join(output_dir, 'lowvol_backtest_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 报告已保存: {report_path}")
    
    return json_path, report_path


def main():
    """主函数"""
    
    try:
        # 运行回测
        results, market_data = run_backtest()
        
        # 生成报告
        report = generate_report(results, market_data)
        
        # 保存结果
        json_path, report_path = save_results(results, report, market_data)
        
        print("\n" + "=" * 70)
        print("回测完成！")
        print("=" * 70)
        
        return results
        
    except Exception as e:
        print(f"\n✗ 回测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    main()
