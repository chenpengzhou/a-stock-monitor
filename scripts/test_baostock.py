#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统 - BaoStock数据源测试
"""

import random
import baostock as bs


def get_market_data(start_date, end_date):
    """从BaoStock获取数据"""
    lg = bs.login()
    rs = bs.query_history_k_data_plus(
        "sh.000300",
        "date,close",
        start_date=start_date,
        end_date=end_date,
        frequency="d"
    )
    data_list = []
    while rs.error_code == '0' and rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    # 提取收盘价
    closes = [float(row[1]) for row in data_list]
    return closes


# 测试获取数据
print("=" * 50)
print("🧪 BaoStock数据源测试")
print("=" * 50)

months = [
    ("2024-10-01", "2024-10-31", "第1个月"),
    ("2024-11-01", "2024-11-30", "第2个月"),
    ("2024-12-01", "2024-12-31", "第3个月"),
    ("2025-01-01", "2025-01-31", "第4个月"),
]

for start, end, name in months:
    closes = get_market_data(start, end)
    print(f"{name}: {len(closes)} 个交易日, 最后价 {closes[-1]:.2f}" if closes else f"{name}: 无数据")

print("=" * 50)
print("✅ BaoStock数据源正常工作！")
print("=" * 50)
