#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场判断系统 - 高低点法
- 时间窗口：60天
- 判断逻辑：严格版（所有低点都抬高/所有高点都降低）
"""

import random


# 配置
N_DAYS = 60  # 时间窗口


def is_bull_market(highs, lows, n=N_DAYS):
    """
    判断是否牛市
    条件：最近n天，低点一个比一个高
    """
    if len(highs) < n or len(lows) < n:
        return False
    
    recent_lows = lows[-n:]
    
    # 所有低点都抬高
    for i in range(n - 1):
        if recent_lows[i] >= recent_lows[i + 1]:
            return False
    
    return True


def is_bear_market(highs, lows, n=N_DAYS):
    """
    判断是否熊市
    条件：最近n天，高点一个比一个低
    """
    if len(highs) < n or len(lows) < n:
        return False
    
    recent_highs = highs[-n:]
    
    # 所有高点都降低
    for i in range(n - 1):
        if recent_highs[i] <= recent_highs[i + 1]:
            return False
    
    return True


def get_market_type(highs, lows, n=N_DAYS):
    """
    获取市场类型
    返回：bull（牛市）/ bear（熊市）/ neutral（震荡）
    """
    if is_bull_market(highs, lows, n):
        return "bull"
    elif is_bear_market(highs, lows, n):
        return "bear"
    else:
        return "neutral"


def test_with_mock_data():
    """用模拟数据测试"""
    
    print("=" * 60)
    print("🧪 市场判断测试 - 高低点法")
    print("=" * 60)
    
    # 模拟牛市数据（低点不断抬高）
    bull_lows = [100 + i * 2 for i in range(100)]  # 每天低点抬高2块
    bull_highs = [bull_lows[i] + 10 for i in range(100)]  # 高点比低点高10块
    
    print("\n📈 模拟牛市数据（低点不断抬高）:")
    print(f"   第1天低点: {bull_lows[0]}")
    print(f"   第60天低点: {bull_lows[59]}")
    print(f"   判断结果: {get_market_type(bull_highs, bull_lows)}")
    
    # 模拟熊市数据（高点不断降低）
    bear_highs = [300 - i * 2 for i in range(100)]  # 每天高点降低2块
    bear_lows = [bear_highs[i] - 10 for i in range(100)]  # 低点比高点低10块
    
    print("\n📉 模拟熊市数据（高点不断降低）:")
    print(f"   第1天高点: {bear_highs[0]}")
    print(f"   第60天高点: {bear_highs[59]}")
    print(f"   判断结果: {get_market_type(bear_highs, bear_lows)}")
    
    # 模拟震荡数据（无明显趋势）
    neutral_highs = [150 + random.uniform(-10, 10) for _ in range(100)]
    neutral_lows = [140 + random.uniform(-10, 10) for _ in range(100)]
    
    print("\n📊 模拟震荡数据（无明显趋势）:")
    recent_highs = neutral_highs[-60:]
    recent_lows = neutral_lows[-60:]
    print(f"   高点范围: {min(recent_highs):.2f} ~ {max(recent_highs):.2f}")
    print(f"   低点范围: {min(recent_lows):.2f} ~ {max(recent_lows):.2f}")
    print(f"   判断结果: {get_market_type(neutral_highs, neutral_lows)}")


if __name__ == "__main__":
    test_with_mock_data()
