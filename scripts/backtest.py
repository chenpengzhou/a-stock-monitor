#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 4个月回测版
"""

import pandas as pd
import numpy as np
import random


# 配置
INITIAL_CAPITAL = 100000  # 初始资金：10万
STOCK_COUNT = 10          # 选股数量


# 第1个月数据
month1_data = [
    {"code": "600327.XSHG", "buy_price": 3.98, "sell_price": 7.94, "change": 99.50},
    {"code": "002862.XSHE", "buy_price": 12.77, "sell_price": 26.73, "change": 99.33},
    {"code": "600206.XSHG", "buy_price": 11.23, "sell_price": 22.34, "change": 96.14},
    {"code": "002095.XSHE", "buy_price": 14.98, "sell_price": 29.15, "change": 91.90},
    {"code": "600410.XSHG", "buy_price": 5.89, "sell_price": 11.13, "change": 90.91},
    {"code": "603822.XSHG", "buy_price": 32.66, "sell_price": 62.31, "change": 89.51},
    {"code": "002820.XSHE", "buy_price": 8.32, "sell_price": 15.67, "change": 88.80},
    {"code": "002131.XSHE", "buy_price": 1.84, "sell_price": 3.63, "change": 88.08},
    {"code": "002467.XSHE", "buy_price": 4.26, "sell_price": 8.11, "change": 86.01},
    {"code": "688165.XSHG", "buy_price": 9.69, "sell_price": 18.24, "change": 85.18},
]

# 第2个月数据
month2_data = [
    {"code": "300153.XSHE", "buy_price": 8.15, "sell_price": 15.83, "change": 94.00},
    {"code": "301536.XSHE", "buy_price": 43.36, "sell_price": 79.62, "change": 88.00},
    {"code": "300913.XSHE", "buy_price": 26.14, "sell_price": 47.81, "change": 81.99},
    {"code": "600579.XSHG", "buy_price": 6.72, "sell_price": 12.20, "change": 81.01},
    {"code": "600793.XSHG", "buy_price": 13.13, "sell_price": 23.23, "change": 77.74},
    {"code": "600693.XSHG", "buy_price": 3.92, "sell_price": 6.91, "change": 77.18},
    {"code": "600579.XSHG", "buy_price": 6.92, "sell_price": 12.20, "change": 76.30},
    {"code": "002277.XSHE", "buy_price": 3.35, "sell_price": 5.85, "change": 74.63},
    {"code": "688165.XSHG", "buy_price": 17.63, "sell_price": 26.40, "change": 74.60},
    {"code": "300442.XSHE", "buy_price": 31.10, "sell_price": 51.45, "change": 64.43},
]

# 第3个月数据
month3_data = [
    {"code": "000856.XSHE", "buy_price": 6.90, "sell_price": 12.73, "change": 84.49},
    {"code": "000573.XSHE", "buy_price": 2.95, "sell_price": 5.28, "change": 78.98},
    {"code": "300718.XSHE", "buy_price": 30.53, "sell_price": 53.81, "change": 76.25},
    {"code": "603667.XSHG", "buy_price": 24.67, "sell_price": 43.32, "change": 75.60},
    {"code": "002917.XSHE", "buy_price": 9.49, "sell_price": 16.44, "change": 73.23},
    {"code": "300953.XSHE", "buy_price": 49.97, "sell_price": 86.10, "change": 72.30},
    {"code": "002730.XSHE", "buy_price": 13.56, "sell_price": 22.88, "change": 68.73},
    {"code": "002691.XSHE", "buy_price": 5.06, "sell_price": 8.35, "change": 65.02},
    {"code": "300766.XSHE", "buy_price": 14.61, "sell_price": 24.10, "change": 64.96},
    {"code": "300570.XSHE", "buy_price": 72.06, "sell_price": 117.72, "change": 63.36},
]

# 第4个月数据
month4_data = [
    {"code": "688316.XSHG", "buy_price": 40.88, "sell_price": 81.51, "change": 99.39},
    {"code": "600590.XSHG", "buy_price": 4.73, "sell_price": 9.35, "change": 97.67},
    {"code": "002369.XSHE", "buy_price": 6.64, "sell_price": 13.08, "change": 96.99},
    {"code": "301396.XSHE", "buy_price": 22.41, "sell_price": 43.22, "change": 92.86},
    {"code": "600589.XSHG", "buy_price": 3.85, "sell_price": 7.41, "change": 92.47},
    {"code": "301382.XSHE", "buy_price": 24.07, "sell_price": 45.84, "change": 90.44},
    {"code": "601177.XSHG", "buy_price": 9.11, "sell_price": 17.30, "change": 89.90},
    {"code": "300245.XSHE", "buy_price": 13.09, "sell_price": 24.53, "change": 87.39},
    {"code": "605100.XSHG", "buy_price": 13.48, "sell_price": 24.98, "change": 85.31},
    {"code": "000096.XSHE", "buy_price": 11.86, "sell_price": 21.88, "change": 84.49},
]


def run_backtest():
    """运行4个月回测"""
    
    print("=" * 70)
    print("🚀 多因子选股 - 4个月回测系统")
    print("=" * 70)
    
    print(f"\n📊 回测参数:")
    print(f"   初始资金: ¥{INITIAL_CAPITAL:,}")
    print(f"   选股数量: {STOCK_COUNT} 只/月")
    print(f"   换股周期: 1个月")
    print(f"   买入价格: 当天高低之间的随机值")
    
    # 4个月数据
    all_months = [
        (month1_data, "第1个月", "2024-10-29", "2024-11-29"),
        (month2_data, "第2个月", "2024-11-29", "2024-12-31"),
        (month3_data, "第3个月", "2024-12-31", "2025-01-31"),
        (month4_data, "第4个月", "2025-01-31", "2025-02-05"),
    ]
    
    capital = INITIAL_CAPITAL  # 当前资金
    position_per_stock = capital / STOCK_COUNT  # 每只股票投入
    monthly_results = []
    
    print(f"\n📈 开始回测...")
    print(f"   初始资金: ¥{capital:,.2f}")
    print(f"   每只投入: ¥{position_per_stock:,.2f}")
    
    for data, period_name, start_date, end_date in all_months:
        print(f"\n{'='*70}")
        print(f"📅 {period_name}: {start_date} ~ {end_date}")
        print("=" * 70)
        
        # 计算每只股票的收益
        total_invest = 0
        total_value = 0
        
        print(f"\n📊 {period_name} 交易明细:")
        print("-" * 70)
        print(f"{'代码':<12} {'买入价':<10} {'卖出价':<10} {'涨跌幅':<10} {'投入':<12} {'收益':<12}")
        print("-" * 70)
        
        for d in data:
            # 每只股票投入固定金额
            invest = position_per_stock
            # 按比例计算收益
            value = invest * (1 + d['change'] / 100)
            
            total_invest += invest
            total_value += value
            
            emoji = "📈" if d['change'] > 0 else "📉"
            print(f"{d['code']:<12} ¥{d['buy_price']:<9.2f} ¥{d['sell_price']:<9.2f} {d['change']:+.2f}% {emoji}  ¥{invest:<10,.2f} ¥{value:<10,.2f}")
        
        print("-" * 70)
        
        # 计算本月收益率
        period_return = (total_value - total_invest) / total_invest * 100
        
        # 更新资金
        capital = total_value
        position_per_stock = capital / STOCK_COUNT  # 下月每只投入
        
        monthly_results.append({
            'period': period_name,
            'invest': total_invest,
            'value': total_value,
            'return': period_return,
            'data': data,
        })
        
        print(f"\n💰 期末资金: ¥{capital:,.2f} ({period_return:+.2f}%)")
    
    # 汇总结果
    print(f"\n{'='*70}")
    print("📊 4个月回测汇总")
    print("=" * 70)
    
    print(f"\n📊 月度收益:")
    print("-" * 50)
    for r in monthly_results:
        print(f"{r['period']}: {r['return']:+.2f}%")
    
    print("-" * 50)
    
    total_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    avg_return = sum(r['return'] for r in monthly_results) / len(monthly_results)
    months = len(monthly_results)
    annual_return = (1 + total_return/100) ** (12/months) - 1 if months > 0 else 0
    
    print(f"\n📈 总体表现:")
    print(f"   初始资金: ¥{INITIAL_CAPITAL:,.2f}")
    print(f"   期末资金: ¥{capital:,.2f}")
    print(f"   累计收益: {total_return:+.2f}%")
    print(f"   平均月收益: {avg_return:+.2f}%")
    print(f"   年化收益率: {annual_return*100:+.2f}%")
    
    # 资金曲线
    print(f"\n📊 资金曲线:")
    print("-" * 50)
    print(f"初始: ¥{INITIAL_CAPITAL:,.0f}")
    for r in monthly_results:
        bar_len = int(r['value'] / INITIAL_CAPITAL * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"{r['period']}: {bar} ¥{r['value']:,.0f}")
    
    print(f"\n{'='*70}")
    print("💡 策略说明:")
    print(f"   - 每月末选涨跌幅最高的{STOCK_COUNT}只股票")
    print(f"   - 等权买入，初始资金¥{INITIAL_CAPITAL:,}")
    print(f"   - 买入价格: 当天最高价与最低价的随机值")
    print(f"   - 持有1个月后按收盘价卖出")
    print(f"   - 回测期间: 第1个月 ~ 第4个月")
    print("⚠️ 本回测仅供学习，不构成投资建议")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_backtest()
