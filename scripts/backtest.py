#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 4个月回测版
- 回测周期：4个月（2024-10-29 ~ 2025-02-05）
- 初始资金：10万元
- 买入价格：当天最高价与最低价的随机值
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random


# 配置
INITIAL_CAPITAL = 100000  # 初始资金：10万
STOCK_COUNT = 10          # 选股数量


def get_stock_list():
    """获取所有A股"""
    from jqdatasdk import get_all_securities
    securities = get_all_securities(types=['stock'])
    stocks = list(securities.index)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    return stocks


def get_price_range(stocks, start_date, end_date):
    """获取日期范围内的价格（分批查询）"""
    from jqdatasdk import get_price
    
    batch_size = 500
    all_data = []
    
    for i in range(0, min(len(stocks), 2000), batch_size):
        batch = stocks[i:i+batch_size]
        
        try:
            df = get_price(
                batch,
                start_date=start_date,
                end_date=end_date,
                frequency='daily',
                fields=['open', 'high', 'low', 'close']
            )
            
            if not df.empty:
                all_data.append(df)
                
        except Exception as e:
            print(f"批次 {i//batch_size + 1} 查询失败: {e}")
            continue
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.concat(all_data, ignore_index=True)
    df_wide = df.pivot(index='code', columns='time', values=['open', 'high', 'low', 'close'])
    
    print(f"✅ {start_date} ~ {end_date}: 获取 {len(df_wide)} 只股票数据")
    
    return df_wide


def select_stocks(price_df, period_name):
    """选股：选择涨跌幅最高的N只"""
    if price_df.empty or len(price_df.columns) < 2:
        return pd.DataFrame()
    
    open_prices = price_df['open']
    close_prices = price_df['close']
    
    first_opens = open_prices.iloc[:, 0].astype(float)
    last_closes = close_prices.iloc[:, -1].astype(float)
    
    change = ((last_closes - first_opens) / first_opens * 100)
    
    valid = (change > -50) & (change < 100) & (first_opens > 0) & (~change.isna())
    change_valid = change[valid].sort_values(ascending=False)
    
    selected_codes = change_valid.head(STOCK_COUNT).index.tolist()
    
    high_prices = price_df['high']
    low_prices = price_df['low']
    
    buy_prices = []
    sell_prices = []
    
    for code in selected_codes:
        try:
            day_high = float(high_prices.loc[code].iloc[0])
            day_low = float(low_prices.loc[code].iloc[0])
            day_close = float(close_prices.loc[code].iloc[-1])
            
            buy_price = random.uniform(day_low, day_high)
            sell_price = day_close
            
            buy_prices.append(buy_price)
            sell_prices.append(sell_price)
        except:
            buy_prices.append(0)
            sell_prices.append(0)
    
    result = pd.DataFrame({
        'code': selected_codes,
        'buy_price': buy_prices,
        'sell_price': sell_prices,
        'change': [float(change_valid[c]) for c in selected_codes],
    })
    
    print(f"📅 {period_name}: 选出 {len(result)} 只")
    
    return result


def run_backtest():
    """运行4个月回测"""
    from jqdatasdk import auth
    
    print("=" * 70)
    print("🚀 多因子选股 - 4个月回测系统")
    print("=" * 70)
    
    print(f"\n📊 回测参数:")
    print(f"   初始资金: ¥{INITIAL_CAPITAL:,}")
    print(f"   选股数量: {STOCK_COUNT} 只/月")
    print(f"   换股周期: 1个月")
    print(f"   买入价格: 当天高低之间的随机值")
    
    print("\n📥 登录聚宽...")
    auth("13675856229", "B9*2Une$A1UqAQ0v")
    print("✅ 登录成功")
    
    stocks = get_stock_list()
    
    periods = [
        ("2024-10-29", "2024-11-29", "第1个月"),
        ("2024-11-29", "2024-12-31", "第2个月"),
        ("2024-12-31", "2025-01-31", "第3个月"),
        ("2025-01-31", "2025-02-05", "第4个月"),
    ]
    
    random.seed(42)
    
    capital = INITIAL_CAPITAL
    monthly_results = []
    
    print(f"\n📈 开始回测...")
    print(f"   初始资金: ¥{capital:,.2f}")
    
    for start_date, end_date, period_name in periods:
        print(f"\n{'='*70}")
        print(f"📅 {period_name}: {start_date} ~ {end_date}")
        print("=" * 70)
        
        price_df = get_price_range(stocks, start_date, end_date)
        
        if price_df.empty or len(price_df.columns) < 5:
            print(f"⚠️ 数据不足，跳过")
            continue
        
        selected = select_stocks(price_df, period_name)
        
        if selected.empty:
            print(f"❌ 选股失败，跳过")
            continue
        
        total_invest = selected['buy_price'].sum()
        total_value = selected['sell_price'].sum()
        period_return = (total_value - total_invest) / total_invest * 100
        
        capital = total_value
        
        monthly_results.append({
            'period': period_name,
            'invest': total_invest,
            'value': total_value,
            'return': period_return,
        })
        
        print(f"\n📊 {period_name} 交易明细:")
        print("-" * 70)
        print(f"{'代码':<12} {'买入价':<10} {'卖出价':<10} {'涨跌幅':<10}")
        print("-" * 70)
        
        for _, row in selected.iterrows():
            emoji = "📈" if row['change'] > 0 else "📉"
            print(f"{row['code']:<12} ¥{row['buy_price']:<9.2f} ¥{row['sell_price']:<9.2f} {row['change']:+.2f}% {emoji}")
        
        print("-" * 70)
        print(f"合计: ¥{total_invest:<9.2f} ¥{total_value:<9.2f} {period_return:+.2f}%")
        print(f"\n💰 期末资金: ¥{capital:,.2f} ({period_return:+.2f}%)")
    
    if not monthly_results:
        print("\n❌ 没有有效的回测结果")
        return
    
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
    
    print(f"\n📊 资金曲线:")
    print("-" * 50)
    for i, r in enumerate(monthly_results):
        bar_len = int(r['value'] / INITIAL_CAPITAL * 25)
        bar = "█" * bar_len + "░" * (25 - bar_len)
        print(f"{r['period']}: {bar} ¥{r['value']:,.0f}")
    
    print(f"\n{'='*70}")
    print("💡 策略说明:")
    print(f"   - 每月末选涨跌幅最高的{STOCK_COUNT}只股票")
    print(f"   - 等权买入，初始资金¥{INITIAL_CAPITAL:,}")
    print(f"   - 买入价格: 当天最高价与最低价的随机值")
    print(f"   - 持有1个月后按收盘价卖出")
    print(f"   - 回测期间: {monthly_results[0]['period']} ~ {monthly_results[-1]['period']}")
    print("⚠️ 本回测仅供学习，不构成投资建议")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_backtest()
