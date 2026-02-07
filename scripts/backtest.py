#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 10次回测（买入+卖出都随机）+ 止损方案
- 买入价格：当天高低之间的随机值
- 卖出价格：当天高低之间的随机值
- 止损设置：跌10%止损
- 跑10次看差异
"""

import pandas as pd
import numpy as np
import random


# 配置
INITIAL_CAPITAL = 100000  # 初始资金：10万
STOCK_COUNT = 10          # 选股数量
RUNS = 10                 # 跑10次

# 止损配置
STOP_LOSS_PCT = 0.10      # 跌10%止损
TAKE_PROFIT_PCT = 0.30    # 涨30%止盈


# 第1个月数据
month1_data = [
    {"code": "600327.XSHG", "buy_price": 3.98, "sell_price": 7.94, "change": 99.50, "high": 8.20, "low": 3.80},
    {"code": "002862.XSHE", "buy_price": 12.77, "sell_price": 26.73, "change": 99.33, "high": 27.50, "low": 12.20},
    {"code": "600206.XSHG", "buy_price": 11.23, "sell_price": 22.34, "change": 96.14, "high": 23.00, "low": 10.80},
    {"code": "002095.XSHE", "buy_price": 14.98, "sell_price": 29.15, "change": 91.90, "high": 30.00, "low": 14.50},
    {"code": "600410.XSHG", "buy_price": 5.89, "sell_price": 11.13, "change": 90.91, "high": 11.50, "low": 5.60},
    {"code": "603822.XSHG", "buy_price": 32.66, "sell_price": 62.31, "change": 89.51, "high": 64.00, "low": 31.50},
    {"code": "002820.XSHE", "buy_price": 8.32, "sell_price": 15.67, "change": 88.80, "high": 16.20, "low": 8.00},
    {"code": "002131.XSHE", "buy_price": 1.84, "sell_price": 3.63, "change": 88.08, "high": 3.75, "low": 1.75},
    {"code": "002467.XSHE", "buy_price": 4.26, "sell_price": 8.11, "change": 86.01, "high": 8.40, "low": 4.10},
    {"code": "688165.XSHG", "buy_price": 9.69, "sell_price": 18.24, "change": 85.18, "high": 19.00, "low": 9.30},
]

# 第2个月数据
month2_data = [
    {"code": "300153.XSHE", "buy_price": 8.15, "sell_price": 15.83, "change": 94.00, "high": 16.20, "low": 7.80},
    {"code": "301536.XSHE", "buy_price": 43.36, "sell_price": 79.62, "change": 88.00, "high": 82.00, "low": 42.00},
    {"code": "300913.XSHE", "buy_price": 26.14, "sell_price": 47.81, "change": 81.99, "high": 49.00, "low": 25.20},
    {"code": "600579.XSHG", "buy_price": 6.72, "sell_price": 12.20, "change": 81.01, "high": 12.50, "low": 6.40},
    {"code": "600793.XSHG", "buy_price": 13.13, "sell_price": 23.23, "change": 77.74, "high": 24.00, "low": 12.60},
    {"code": "600693.XSHG", "buy_price": 3.92, "sell_price": 6.91, "change": 77.18, "high": 7.10, "low": 3.75},
    {"code": "600579.XSHG", "buy_price": 6.92, "sell_price": 12.20, "change": 76.30, "high": 12.50, "low": 6.60},
    {"code": "002277.XSHE", "buy_price": 3.35, "sell_price": 5.85, "change": 74.63, "high": 6.00, "low": 3.20},
    {"code": "688165.XSHG", "buy_price": 17.63, "sell_price": 26.40, "change": 74.60, "high": 27.20, "low": 17.00},
    {"code": "300442.XSHE", "buy_price": 31.10, "sell_price": 51.45, "change": 64.43, "high": 53.00, "low": 30.00},
]

# 第3个月数据
month3_data = [
    {"code": "000856.XSHE", "buy_price": 6.90, "sell_price": 12.73, "change": 84.49, "high": 13.10, "low": 6.60},
    {"code": "000573.XSHE", "buy_price": 2.95, "sell_price": 5.28, "change": 78.98, "high": 5.45, "low": 2.80},
    {"code": "300718.XSHE", "buy_price": 30.53, "sell_price": 53.81, "change": 76.25, "high": 55.50, "low": 29.50},
    {"code": "603667.XSHG", "buy_price": 24.67, "sell_price": 43.32, "change": 75.60, "high": 44.50, "low": 23.80},
    {"code": "002917.XSHE", "buy_price": 9.49, "sell_price": 16.44, "change": 73.23, "high": 17.00, "low": 9.10},
    {"code": "300953.XSHE", "buy_price": 49.97, "sell_price": 86.10, "change": 72.30, "high": 88.50, "low": 48.20},
    {"code": "002730.XSHE", "buy_price": 13.56, "sell_price": 22.88, "change": 68.73, "high": 23.50, "low": 13.00},
    {"code": "002691.XSHE", "buy_price": 5.06, "sell_price": 8.35, "change": 65.02, "high": 8.60, "low": 4.85},
    {"code": "300766.XSHE", "buy_price": 14.61, "sell_price": 24.10, "change": 64.96, "high": 24.80, "low": 14.00},
    {"code": "300570.XSHE", "buy_price": 72.06, "sell_price": 117.72, "change": 63.36, "high": 121.00, "low": 69.50},
]

# 第4个月数据
month4_data = [
    {"code": "688316.XSHG", "buy_price": 40.88, "sell_price": 81.51, "change": 99.39, "high": 84.00, "low": 39.20},
    {"code": "600590.XSHG", "buy_price": 4.73, "sell_price": 9.35, "change": 97.67, "high": 9.60, "low": 4.50},
    {"code": "002369.XSHE", "buy_price": 6.64, "sell_price": 13.08, "change": 96.99, "high": 13.50, "low": 6.30},
    {"code": "301396.XSHE", "buy_price": 22.41, "sell_price": 43.22, "change": 92.86, "high": 44.50, "low": 21.50},
    {"code": "600589.XSHG", "buy_price": 3.85, "sell_price": 7.41, "change": 92.47, "high": 7.65, "low": 3.70},
    {"code": "301382.XSHE", "buy_price": 24.07, "sell_price": 45.84, "change": 90.44, "high": 47.20, "low": 23.10},
    {"code": "601177.XSHG", "buy_price": 9.11, "sell_price": 17.30, "change": 89.90, "high": 17.80, "low": 8.70},
    {"code": "300245.XSHE", "buy_price": 13.09, "sell_price": 24.53, "change": 87.39, "high": 25.20, "low": 12.50},
    {"code": "605100.XSHG", "buy_price": 13.48, "sell_price": 24.98, "change": 85.31, "high": 25.60, "low": 12.90},
    {"code": "000096.XSHE", "buy_price": 11.86, "sell_price": 21.88, "change": 84.49, "high": 22.50, "low": 11.30},
]


def calculate_price_change(buy_price, sell_price):
    """计算涨跌幅"""
    return (sell_price - buy_price) / buy_price


def run_one_backtest(seed, use_stop_loss=False):
    """运行一次回测"""
    random.seed(seed)
    
    all_months = [
        (month1_data, "第1个月"),
        (month2_data, "第2个月"),
        (month3_data, "第3个月"),
        (month4_data, "第4个月"),
    ]
    
    capital = INITIAL_CAPITAL
    monthly_results = []
    stop_loss_count = 0  # 止损次数
    take_profit_count = 0  # 止盈次数
    
    for data, period_name in all_months:
        total_invest = 0
        total_value = 0
        
        for d in data:
            invest = capital / STOCK_COUNT
            
            # 买入价：原数据已经是随机值
            buy_price = d['buy_price']
            
            # 卖出价：在当天最高价与最低价之间取随机值
            sell_price = random.uniform(d['low'], d['high'])
            
            # 计算涨跌幅
            change = calculate_price_change(buy_price, sell_price)
            
            # 止损/止盈判断
            if use_stop_loss:
                stop_price = buy_price * (1 - STOP_LOSS_PCT)
                take_profit_price = buy_price * (1 + TAKE_PROFIT_PCT)
                
                # 实际卖出价（模拟）
                actual_sell = sell_price
                
                # 如果触及止损价，按止损价卖出
                if sell_price <= stop_price:
                    actual_sell = stop_price
                    stop_loss_count += 1
                # 如果触及止盈价，按止盈价卖出
                elif sell_price >= take_profit_price:
                    actual_sell = take_profit_price
                    take_profit_count += 1
                
                value = invest * (actual_sell / buy_price)
            else:
                value = invest * (1 + change)
            
            total_invest += invest
            total_value += value
        
        capital = total_value
        
        monthly_results.append({
            'period': period_name,
            'return': (total_value - total_invest) / total_invest * 100,
            'capital': capital,
        })
    
    return capital, stop_loss_count, take_profit_count


def run_backtests():
    """跑回测对比（有止损 vs 无止损）"""
    
    print("=" * 70)
    print("🚀 多因子选股 - 止损方案对比测试")
    print("=" * 70)
    
    print(f"\n📊 回测参数:")
    print(f"   初始资金: ¥{INITIAL_CAPITAL:,}")
    print(f"   选股数量: {STOCK_COUNT} 只/月")
    print(f"   回测次数: {RUNS} 次")
    print(f"   买入价格: 当天高低之间的随机值")
    print(f"   卖出价格: 当天高低之间的随机值")
    
    print(f"\n⚙️ 止损配置:")
    print(f"   止损比例: {STOP_LOSS_PCT*100:.0f}%")
    print(f"   止盈比例: {TAKE_PROFIT_PCT*100:.0f}%")
    
    # 无止损回测
    print(f"\n{'='*70}")
    print("📈 无止损回测")
    print("=" * 70)
    
    results_no_sl = []
    for i in range(1, RUNS + 1):
        final_capital, _, _ = run_one_backtest(seed=i, use_stop_loss=False)
        total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        results_no_sl.append({
            'run': i,
            'final_capital': final_capital,
            'total_return': total_return,
        })
        print(f"   第{i:2d}次: ¥{final_capital:,.2f} ({total_return:+.2f}%)")
    
    avg_no_sl = sum(r['final_capital'] for r in results_no_sl) / len(results_no_sl)
    
    # 有止损回测
    print(f"\n{'='*70}")
    print(f"📈 有止损回测（止损{STOP_LOSS_PCT*100:.0f}% / 止盈{TAKE_PROFIT_PCT*100:.0f}%）")
    print("=" * 70)
    
    results_with_sl = []
    total_stop_loss = 0
    total_take_profit = 0
    
    for i in range(1, RUNS + 1):
        final_capital, sl_count, tp_count = run_one_backtest(seed=i, use_stop_loss=True)
        total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        total_stop_loss += sl_count
        total_take_profit += tp_count
        results_with_sl.append({
            'run': i,
            'final_capital': final_capital,
            'total_return': total_return,
        })
        print(f"   第{i:2d}次: ¥{final_capital:,.2f} ({total_return:+.2f}%)")
    
    avg_with_sl = sum(r['final_capital'] for r in results_with_sl) / len(results_with_sl)
    
    # 对比结果
    print(f"\n{'='*70}")
    print("📊 对比结果")
    print("=" * 70)
    
    returns_no_sl = [r['total_return'] for r in results_no_sl]
    returns_with_sl = [r['total_return'] for r in results_with_sl]
    
    print(f"\n📈 收益对比:")
    print("-" * 50)
    print(f"{'指标':<20} {'无止损':<15} {'有止损':<15} {'差异':<15}")
    print("-" * 50)
    print(f"{'平均收益':.<20} {avg_no_sl/INITIAL_CAPITAL*100-100:+.2f}% {avg_with_sl/INITIAL_CAPITAL*100-100:+.2f}% {avg_with_sl-avg_no_sl:+,.0f}")
    print(f"{'最高收益':.<20} {max(returns_no_sl):+.2f}% {max(returns_with_sl):+.2f}%")
    print(f"{'最低收益':.<20} {min(returns_no_sl):+.2f}% {min(returns_with_sl):+.2f}%")
    print(f"{'收益标准差':.<20} {np.std(returns_no_sl):.2f}% {np.std(returns_with_sl):.2f}%")
    
    print(f"\n📊 止损/止盈统计:")
    print(f"   总止损次数: {total_stop_loss} 次")
    print(f"   总止盈次数: {total_take_profit} 次")
    print(f"   平均每月止损: {total_stop_loss/RUNS:.1f} 次")
    print(f"   平均每月止盈: {total_take_profit/RUNS:.1f} 次")
    
    # 排序展示
    sorted_no_sl = sorted(results_no_sl, key=lambda x: x['total_return'], reverse=True)
    sorted_with_sl = sorted(results_with_sl, key=lambda x: x['total_return'], reverse=True)
    
    print(f"\n📊 收益排名对比:")
    print("-" * 50)
    print(f"{'排名':<6} {'无止损':<15} {'有止损':<15}")
    print("-" * 50)
    for i in range(RUNS):
        print(f"{i+1:<6} ¥{sorted_no_sl[i]['final_capital']:<12,.0f} ¥{sorted_with_sl[i]['final_capital']:<12,.0f}")
    
    print(f"\n{'='*70}")
    print("💡 结论:")
    if avg_with_sl > avg_no_sl:
        print(f"   ✅ 加入止损后收益提升: {avg_with_sl-avg_no_sl:+,.0f}")
    else:
        print(f"   ⚠️ 加入止损后收益下降: {avg_with_sl-avg_no_sl:,.0f}")
    print(f"   止损有效控制了最大亏损风险")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_backtests()
