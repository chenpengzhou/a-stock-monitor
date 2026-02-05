#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - 简化版
"""

import pandas as pd
from datetime import datetime


# 配置
STOCK_COUNT = 10
START_DATE = "2025-11-04"


def get_all_stocks():
    """获取所有A股"""
    from jqdatasdk import get_all_securities
    securities = get_all_securities(types=['stock'])
    stocks = list(securities.index)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    return stocks


def get_price_data(stocks):
    """获取收盘价"""
    from jqdatasdk import get_price
    
    df = get_price(stocks, start_date=START_DATE, end_date="2025-11-05",
                   frequency='daily', fields=['close'])
    
    df_wide = df.pivot(index='code', columns='time', values='close')
    last_date = df_wide.columns[-1]
    df_final = df_wide[[last_date]].copy()
    df_final.columns = ['close']
    df_final = df_final.dropna()
    
    # 计算涨跌幅
    first_date = df_wide.columns[0]
    df_final['change'] = (df_wide[last_date] - df_wide[first_date]) / df_wide[first_date] * 100
    
    print(f"✅ 获取行情成功 ({len(df_final)} 只)")
    return df_final


def select_stocks(price_df):
    """选股"""
    print("🔍 选股中...")
    
    results = []
    
    for code in list(price_df.index):
        try:
            results.append({
                "code": code.split('.')[0],
                "price": float(price_df.loc[code, 'close']),
                "change": float(price_df.loc[code, 'change']),
            })
        except:
            continue
    
    print(f"📊 处理 {len(results)} 只股票")
    
    # 按涨跌幅排序
    results.sort(key=lambda x: x["change"], reverse=True)
    selected = results[:STOCK_COUNT]
    print(f"✅ 选出 {len(selected)} 只")
    return selected


def print_report(selected):
    """打印报告"""
    print(f"\n{'='*50}")
    print(f"📊 多因子选股报告 - {START_DATE}")
    print(f"{'='*50}")
    
    for i, s in enumerate(selected, 1):
        emoji = "📈" if s["change"] > 0 else "📉"
        print(f"{i:2d}. {s['code']} | ¥{s['price']:.2f} {emoji} {s['change']:+.2f}%")
    
    print(f"{'='*50}")
    print("💡 数据来源：聚宽JQData")
    print("💡 选股因子：近1月涨跌幅")
    print("⚠️ 本报告仅供分析，不构成投资建议")


def run():
    """主函数"""
    from jqdatasdk import auth
    
    print("="*50)
    print("🚀 多因子选股系统")
    print("="*50)
    
    print("\n📥 登录聚宽...")
    auth("13675856229", "B9*2Une$A1UqAQ0v")
    print("✅ 登录成功")
    
    stocks = get_all_stocks()
    price_df = get_price_data(stocks)
    selected = select_stocks(price_df)
    print_report(selected)


if __name__ == "__main__":
    run()
