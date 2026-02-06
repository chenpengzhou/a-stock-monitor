#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 回测版
换股周期：1个月
"""

import pandas as pd
import numpy as np
from datetime import datetime


# 配置
STOCK_COUNT = 10


def get_stock_list():
    """获取所有A股"""
    from jqdatasdk import get_all_securities
    securities = get_all_securities(types=['stock'])
    stocks = list(securities.index)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    return stocks


def get_price_range(stocks, start_date, end_date):
    """获取日期范围内的价格"""
    from jqdatasdk import get_price
    
    df = get_price(
        stocks,
        start_date=start_date,
        end_date=end_date,
        frequency='daily',
        fields=['close']
    )
    
    df_wide = df.pivot(index='code', columns='time', values='close')
    
    print(f"✅ {start_date} ~ {end_date}: {len(df_wide.columns)} 交易日")
    
    return df_wide


def select_stocks(price_df, period_name):
    """选股：选择涨跌幅最高的N只"""
    if price_df.empty or len(price_df.columns) < 2:
        return pd.DataFrame()
    
    # 获取首尾价格
    first_col = price_df.columns[0]
    last_col = price_df.columns[-1]
    
    first_prices = price_df[first_col].astype(float)
    last_prices = price_df[last_col].astype(float)
    
    # 计算涨跌幅
    change = ((last_prices - first_prices) / first_prices * 100)
    
    # 过滤无效数据
    valid = (change > -50) & (change < 100) & (first_prices > 0) & (~change.isna())
    
    # 筛选并排序
    change_valid = change[valid].sort_values(ascending=False)
    
    # 选前N只
    selected_codes = change_valid.head(STOCK_COUNT).index.tolist()
    
    # 构建结果
    result = pd.DataFrame({
        'code': selected_codes,
        'price_start': [float(first_prices[c]) for c in selected_codes],
        'price_end': [float(last_prices[c]) for c in selected_codes],
        'change': [float(change_valid[c]) for c in selected_codes],
    })
    
    print(f"📅 {period_name}: 选出 {len(result)} 只")
    
    return result


def run_backtest():
    """运行回测"""
    from jqdatasdk import auth
    
    print("=" * 60)
    print("🚀 多因子选股回测系统")
    print("=" * 60)
    
    print("\n📥 登录聚宽...")
    auth("13675856229", "B9*2Une$A1UqAQ0v")
    print("✅ 登录成功")
    
    stocks = get_stock_list()
    
    # 回测周期
    periods = [
        ("2024-10-29", "2024-11-29", "第1个月"),
        ("2024-11-29", "2024-12-31", "第2个月"),
        ("2024-12-31", "2025-01-31", "第3个月"),
        ("2025-01-31", "2025-02-28", "第4个月"),
    ]
    
    print(f"\n📊 回测: {len(periods)} 个月 | 每月选 {STOCK_COUNT} 只 | 换股周期: 1个月")
    
    results = []
    
    for start_date, end_date, period_name in periods:
        print(f"\n{'='*60}")
        print(f"📅 {period_name}: {start_date} ~ {end_date}")
        print("=" * 60)
        
        price_df = get_price_range(stocks, start_date, end_date)
        
        if price_df.empty or len(price_df.columns) < 5:
            print(f"⚠️ 数据不足，跳过")
            continue
        
        selected = select_stocks(price_df, period_name)
        
        if selected.empty:
            print(f"❌ 选股失败")
            continue
        
        # 计算收益
        total_invest = selected['price_start'].sum()
        total_value = selected['price_end'].sum()
        period_return = (total_value - total_invest) / total_invest * 100
        
        results.append({
            'period': period_name,
            'invest': total_invest,
            'value': total_value,
            'return': period_return,
        })
        
        print(f"\n📈 收益: {period_return:+.2f}%")
        print(f"   投入: ¥{total_invest:.2f} → 价值: ¥{total_value:.2f}")
        
        # 显示选中股票
        for _, row in selected.iterrows():
            emoji = "📈" if row['change'] > 0 else "📉"
            print(f"   {row['code']}: ¥{row['price_start']:.2f} → ¥{row['price_end']:.2f} {emoji} {row['change']:+.2f}%")
    
    if not results:
        print("\n❌ 无有效回测结果")
        return
    
    # 汇总
    print(f"\n{'='*60}")
    print("📊 回测汇总")
    print("=" * 60)
    
    for r in results:
        print(f"{r['period']}: {r['return']:+.2f}%")
    
    total_return = sum(r['return'] for r in results)
    avg_return = total_return / len(results)
    annual_return = (1 + avg_return/100) ** 12 - 1
    
    print(f"\n📈 总体表现:")
    print(f"   累计收益: {total_return:+.2f}%")
    print(f"   平均月收益: {avg_return:+.2f}%")
    print(f"   年化收益率: {annual_return*100:+.2f}%")
    
    print(f"\n{'='*60}")
    print("💡 策略说明:")
    print("   - 每月末选涨跌幅最高的10只")
    print("   - 等权买入，持有1个月")
    print(f"   - 回测期间: {results[0]['period']} ~ {results[-1]['period']}")
    print("⚠️ 本回测仅供学习，不构成投资建议")


if __name__ == "__main__":
    run_backtest()
