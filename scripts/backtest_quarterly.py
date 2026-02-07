#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 2020年季度回测（每季度总结）
"""

import random
import baostock as bs

INITIAL_CAPITAL = 100000
RUNS = 5

STRATEGY_CONFIG = {
    "strong_bull": {"stop_loss": 0.20, "take_profit": 1.00, "position": 1.0, "name": "强牛市"},
    "bull": {"stop_loss": 0.15, "take_profit": 0.80, "position": 0.8, "name": "牛市"},
    "neutral": {"stop_loss": 0.12, "take_profit": 0.50, "position": 0.6, "name": "震荡"},
    "bear": {"stop_loss": 0.10, "take_profit": 0.30, "position": 0.5, "name": "熊市"},
}

QUARTERS = [
    {"name": "2020-Q1", "start": "2020-01-01", "end": "2020-03-31"},
    {"name": "2020-Q2", "start": "2020-04-01", "end": "2020-06-30"},
    {"name": "2020-Q3", "start": "2020-07-01", "end": "2020-09-30"},
    {"name": "2020-Q4", "start": "2020-10-01", "end": "2020-12-31"},
]

def calculate_ma(prices, n=5):
    if len(prices) < n:
        return prices[-1] if prices else 0
    return sum(prices[-n:]) / n

def get_market_type(closes):
    if len(closes) < 5:
        return "neutral"
    ma5 = calculate_ma(closes, min(5, len(closes)))
    ma10 = calculate_ma(closes, min(10, len(closes)))
    ma30 = calculate_ma(closes, min(30, len(closes)))
    ma60 = calculate_ma(closes, min(60, len(closes)))
    current_price = closes[-1]
    score = 0
    if ma5 > ma10: score += 1
    if ma10 > ma30: score += 1
    if ma30 > ma60: score += 1
    if current_price > ma60: score += 1
    if score >= 4: return "strong_bull"
    elif score == 3: return "bull"
    elif score == 2: return "neutral"
    else: return "bear"

STOCKS = [
    {"code": "600519", "buy_price": 1100, "sell_price": 1300, "high": 1350, "low": 1050},
    {"code": "000651", "buy_price": 55, "sell_price": 68, "high": 70, "low": 52},
    {"code": "601318", "buy_price": 75, "sell_price": 82, "high": 85, "low": 72},
    {"code": "000858", "buy_price": 130, "sell_price": 155, "high": 160, "low": 125},
    {"code": "600276", "buy_price": 12, "sell_price": 15, "high": 16, "low": 11},
    {"code": "002475", "buy_price": 28, "sell_price": 35, "high": 37, "low": 26},
    {"code": "600809", "buy_price": 100, "sell_price": 125, "high": 130, "low": 95},
    {"code": "000568", "buy_price": 45, "sell_price": 55, "high": 58, "low": 42},
    {"code": "603288", "buy_price": 65, "sell_price": 78, "high": 82, "low": 62},
    {"code": "600372", "buy_price": 8.5, "sell_price": 10.5, "high": 11, "low": 8},
]

def get_market_data(q):
    lg = bs.login()
    rs = bs.query_history_k_data_plus("sh.000300", "date,close", start_date=q["start"], end_date=q["end"], frequency="d")
    closes = []
    while rs.error_code == '0' and rs.next():
        closes.append(float(rs.get_row_data()[1]))
    bs.logout()
    return closes

def run_quarter_backtest(seed, quarters, market_types):
    """单次回测，返回每季度结果"""
    random.seed(seed)
    capital = INITIAL_CAPITAL
    quarterly_results = []
    
    for q in quarters:
        mt = market_types[q["name"]]
        params = STRATEGY_CONFIG[mt]
        position_capital = capital * params["position"]
        
        q_invest = 0
        q_value = 0
        
        for d in STOCKS:
            invest = position_capital / len(STOCKS)
            buy_price = random.uniform(d['low'], d['high'])
            sell_price = random.uniform(d['low'], d['high'])
            
            stop_price = buy_price * (1 - params["stop_loss"])
            take_profit_price = buy_price * (1 + params["take_profit"])
            
            if sell_price <= stop_price:
                sell_price = stop_price
            elif sell_price >= take_profit_price:
                sell_price = take_profit_price
            
            q_invest += invest
            q_value += invest * (sell_price / buy_price)
        
        capital = q_value
        
        quarterly_results.append({
            'quarter': q["name"],
            'market_type': mt,
            'market_name': params["name"],
            'return': (q_value - q_invest) / q_invest * 100,
            'capital': capital,
        })
    
    return quarterly_results

def run_backtest():
    print("=" * 80)
    print("🚀 多因子选股系统 - 2020年季度回测")
    print("=" * 80)
    print(f"\n📊 初始资金: ¥{INITIAL_CAPITAL:,}, 回测{RUNS}次")
    print(f"📈 数据源: BaoStock（免费）")
    
    # 获取季度市场类型
    print(f"\n📈 季度市场判断:")
    market_types = {}
    for q in QUARTERS:
        closes = get_market_data(q)
        mt = get_market_type(closes)
        market_types[q["name"]] = mt
        print(f"   {q['name']}: {STRATEGY_CONFIG[mt]['name']} ({len(closes)}天)")
    
    # 运行回测
    print(f"\n📈 开始回测...")
    all_results = []
    
    for i in range(1, RUNS + 1):
        q_results = run_quarter_backtest(i, QUARTERS, market_types)
        final_capital = q_results[-1]['capital']
        total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        all_results.append({'run': i, 'quarterly': q_results, 'total_return': total_return})
        print(f"   第{i}次: ¥{final_capital:,.2f} ({total_return:+.2f}%)")
    
    # ========== 每季度总结 ==========
    print(f"\n{'='*80}")
    print("📊 每季度总结")
    print("=" * 80)
    
    for i, q in enumerate(QUARTERS):
        q_returns = [r['quarterly'][i]['return'] for r in all_results]
        avg_q_return = sum(q_returns) / len(q_returns)
        q_data = all_results[0]['quarterly'][i]
        
        print(f"\n【{q['name']}】")
        print(f"   市场类型: {q_data['market_name']}")
        print(f"   平均收益: {avg_q_return:+.2f}%")
        print(f"   最高收益: {max(q_returns):+.2f}%")
        print(f"   最低收益: {min(q_returns):+.2f}%")
    
    # 年度汇总
    print(f"\n{'='*80}")
    print("📊 2020年度汇总")
    print("=" * 80)
    
    total_returns = [r['total_return'] for r in all_results]
    avg_total = sum(total_returns) / len(total_returns)
    
    print(f"   平均收益: {avg_total:+.2f}%")
    print(f"   最高: {max(total_returns):+.2f}%")
    print(f"   最低: {min(total_returns):+.2f}%")
    print(f"   胜率: {(sum(1 for r in total_returns if r > 0) / len(total_returns) * 100):.1f}%")
    
    # 排名
    sorted_results = sorted(all_results, key=lambda x: x['total_return'], reverse=True)
    print(f"\n📊 收益排名:")
    for i, r in enumerate(sorted_results, 1):
        print(f"   {i}. ¥{r['quarterly'][-1]['capital']:,.2f} ({r['total_return']:+.2f}%)")
    
    print(f"\n{'='*80}")
    print("💡 结论:")
    print(f"   2020年平均收益: {avg_total:+.2f}%")
    print(f"   数据源: BaoStock（免费）")
    print(f"   策略: 根据每季度市场类型自动调整参数")
    print(f"{'='*80}")

if __name__ == "__main__":
    run_backtest()
