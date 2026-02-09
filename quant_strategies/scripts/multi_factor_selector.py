#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统
时区: Asia/Shanghai (UTC+8)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# 配置
STOCK_COUNT = 10

# 账号权限范围内：2024-10-29 到 2025-11-05
START_DATE = "2025-11-04"

# 获取今天的日期（UTC+8）
def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def get_all_stocks():
    """获取所有A股"""
    from jqdatasdk import get_all_securities
    securities = get_all_securities(types=['stock'])
    stocks = list(securities.index)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    return stocks


def get_price_and_change(stocks):
    """获取价格和涨跌幅"""
    from jqdatasdk import get_price
    
    # 权限范围内：2024-10-29 到 2025-11-05
    end_date = "2025-11-05"
    
    df = get_price(stocks, start_date=START_DATE, end_date=end_date,
                   frequency='daily', fields=['close'])
    
    if df.empty or len(df) < 2:
        print(f"⚠️ {START_DATE} 数据不足")
        return pd.DataFrame()
    
    df_wide = df.pivot(index='code', columns='time', values='close')
    
    if len(df_wide.columns) < 2:
        print("⚠️ 交易日不足2个")
        return pd.DataFrame()
    
    first_date = df_wide.columns[0]
    last_date = df_wide.columns[-1]
    
    df_result = pd.DataFrame({
        'price': df_wide[last_date],
        'change': (df_wide[last_date] - df_wide[first_date]) / df_wide[first_date] * 100
    })
    
    df_result = df_result.dropna()
    
    print(f"✅ 获取行情成功 ({len(df_result)} 只)")
    print(f"📅 数据日期: {first_date} ~ {last_date} (UTC+8)")
    
    return df_result


def get_financial_data(stock_codes):
    """获取财务数据"""
    try:
        import pymysql
        
        JQ_CONFIG = {
            'host': 'stock.jqdata.net',
            'port': 3306,
            'user': 'jqdata',
            'password': 'jqdata',
            'database': 'jqdata'
        }
        
        conn = pymysql.connect(**JQ_CONFIG)
        
        stock_list = []
        for code in stock_codes:
            if code.endswith('.XSHG'):
                stock_list.append(f"'{code.replace('.XSHG', '')}'")
            elif code.endswith('.XSHE'):
                stock_list.append(f"'{code.replace('.XSHE', '')}'")
        
        stocks_str = ','.join(stock_list[:100])
        
        sql = f"SELECT code, ROE, pe_ttm as pe, pb FROM common_basic WHERE code IN ({stocks_str}) AND date = '2025-09-30'"
        
        df = pd.read_sql(sql, conn)
        df = df.set_index('code')
        conn.close()
        
        print(f"✅ 获取财务数据成功 ({len(df)} 只)")
        return df
        
    except Exception as e:
        print(f"❌ 获取财务数据失败: {e}")
        return pd.DataFrame()


def calculate_score(row):
    """计算综合得分"""
    score = 50
    
    change = row.get('change', 0)
    if pd.notna(change):
        score += min(max(change, -20), 20) * 0.5
    
    roe = row.get('ROE', 0)
    if pd.notna(roe) and roe > 0:
        score += min(roe, 30) * 0.5
    
    pe = row.get('pe', 0)
    if pd.notna(pe) and pe > 0 and pe < 100:
        score += (100 - pe) * 0.1
    
    pb = row.get('pb', 0)
    if pd.notna(pb) and pb > 0 and pb < 20:
        score += (20 - pb) * 0.2
    
    return min(100, max(0, score))


def select_stocks(price_df, stock_codes):
    """选股"""
    print("🔍 开始多因子选股...")
    
    price_df = price_df[price_df['price'] > 0]
    print(f"📊 有效行情 {len(price_df)} 只")
    
    print("📊 获取财务数据...")
    fin_df = get_financial_data(stock_codes)
    
    results = []
    
    for code in list(price_df.index):
        try:
            if code.endswith('.XSHG'):
                sql_code = code.replace('.XSHG', '')
            elif code.endswith('.XSHE'):
                sql_code = code.replace('.XSHE', '')
            else:
                sql_code = code
            
            row_data = {
                'code': sql_code,
                'price': float(price_df.loc[code, 'price']),
                'change': float(price_df.loc[code, 'change']) if pd.notna(price_df.loc[code, 'change']) else 0,
                'ROE': 0,
                'pe': 0,
                'pb': 0,
            }
            
            if not fin_df.empty and sql_code in fin_df.index:
                row_data['ROE'] = float(fin_df.loc[sql_code, 'ROE']) if pd.notna(fin_df.loc[sql_code, 'ROE']) else 0
                row_data['pe'] = float(fin_df.loc[sql_code, 'pe']) if pd.notna(fin_df.loc[sql_code, 'pe']) else 0
                row_data['pb'] = float(fin_df.loc[sql_code, 'pb']) if pd.notna(fin_df.loc[sql_code, 'pb']) else 0
            
            row_data['score'] = calculate_score(row_data)
            results.append(row_data)
        except:
            continue
    
    print(f"📊 处理 {len(results)} 只股票")
    
    results.sort(key=lambda x: x["score"], reverse=True)
    selected = results[:STOCK_COUNT]
    
    print(f"✅ 选出 {len(selected)} 只股票")
    return selected


def print_report(selected):
    """打印报告"""
    today = get_today()
    
    print(f"\n{'='*60}")
    print(f"📊 多因子选股报告 - {today} (UTC+8)")
    print(f"{'='*60}")
    
    print(f"\n【因子权重】涨跌幅 30% + ROE 40% + PE 20% + PB 10%")
    
    print(f"\n【选股结果】")
    print("-" * 60)
    print(f"{'排名':<4} {'代码':<8} {'价格':<8} {'涨跌幅':<10} {'ROE':<8} {'PE':<8} {'得分':<6}")
    print("-" * 60)
    
    for i, s in enumerate(selected, 1):
        change_emoji = "📈" if s["change"] > 0 else "📉"
        roe_str = f"{s['ROE']:.1f}%" if s['ROE'] > 0 else "N/A"
        pe_str = f"{s['pe']:.1f}" if s['pe'] > 0 else "N/A"
        
        print(f"{i:<4} {s['code']:<8} ¥{s['price']:<7.2f} {s['change']:+.2f}% {change_emoji}  {roe_str:<8} {pe_str:<8} {s['score']:.1f}")
    
    print("-" * 60)
    print("💡 ROE=净资产收益率（越高越好）")
    print("💡 PE=市盈率（越低越好）")
    print(f"{'='*60}")
    print("⚠️ 本报告仅供分析，不构成投资建议")


def run():
    """主函数"""
    from jqdatasdk import auth
    
    print("=" * 60)
    print("🚀 多因子选股系统")
    print("=" * 60)
    print(f"📅 当前日期: {get_today()} (UTC+8)")
    
    print("\n📥 登录聚宽...")
    auth("13675856229", "B9*2Une$A1UqAQ0v")
    print("✅ 登录成功")
    
    stocks = get_all_stocks()
    price_df = get_price_and_change(stocks)
    
    if price_df.empty:
        print("❌ 无法获取行情数据")
        return
    
    selected = select_stocks(price_df, stocks)
    
    if not selected:
        print("❌ 选股失败")
        return
    
    print_report(selected)


if __name__ == "__main__":
    run()
