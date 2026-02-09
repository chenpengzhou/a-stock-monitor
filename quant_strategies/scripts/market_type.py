#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场判断系统 - 综合评分法
- 价格与MA20关系
- 低点抬高/高点降低比例
- 累计涨跌幅
"""

import random


# 配置
N_DAYS = 60  # 时间窗口


def is_bull_market_v1(highs, lows, closes, n=N_DAYS):
    """
    判断是否牛市（原方法：严格版）
    条件：最近n天，低点一个比一个高
    """
    if len(highs) < n or len(lows) < n:
        return False
    
    recent_lows = lows[-n:]
    
    for i in range(n - 1):
        if recent_lows[i] >= recent_lows[i + 1]:
            return False
    
    return True


def is_bear_market_v1(highs, lows, closes, n=N_DAYS):
    """
    判断是否熊市（原方法：严格版）
    条件：最近n天，高点一个比一个低
    """
    if len(highs) < n or len(lows) < n:
        return False
    
    recent_highs = highs[-n:]
    
    for i in range(n - 1):
        if recent_highs[i] <= recent_highs[i + 1]:
            return False
    
    return True


def get_market_type_v1(highs, lows, closes, n=N_DAYS):
    """原版判断"""
    if is_bull_market_v1(highs, lows, closes, n):
        return "bull"
    elif is_bear_market_v1(highs, lows, closes, n):
        return "bear"
    else:
        return "neutral"


def calculate_ma(prices, n=20):
    """计算MA"""
    if len(prices) < n:
        return prices[-1] if prices else 0
    return sum(prices[-n:]) / n


def get_market_type_v2(highs, lows, closes, n=N_DAYS):
    """
    新版判断：综合评分法
    判断逻辑：
    1. 价格与MA20关系（+1/-1/0）
    2. 低点抬高比例（>=60% = +1）
    3. 累计涨跌幅（>3% = +1, <-3% = -1）
    
    总分判断：
    - >= 2 = bull（牛市）
    - <= -1 = bear（熊市）
    - 0~1 = neutral（震荡）
    """
    if len(closes) < n:
        return "neutral"
    
    recent_highs = highs[-n:]
    recent_lows = lows[-n:]
    recent_closes = closes[-n:]
    
    # 1. 价格与MA20关系
    ma20 = calculate_ma(recent_closes, 20)
    current_price = recent_closes[-1]
    
    if current_price > ma20 * 1.02:  # 价格在MA2%以上
        price_score = 1
    elif current_price < ma20 * 0.98:  # 价格在MA2%以下
        price_score = -1
    else:
        price_score = 0
    
    # 2. 低点抬高比例
    low_increase_count = 0
    for i in range(n - 1):
        if recent_lows[i] < recent_lows[i + 1]:
            low_increase_count += 1
    
    low_ratio = low_increase_count / (n - 1)
    if low_ratio >= 0.60:  # 60%低点抬高
        low_score = 1
    elif low_ratio <= 0.40:  # 40%以下低点抬高
        low_score = -1
    else:
        low_score = 0
    
    # 3. 累计涨跌幅
    start_price = recent_closes[0]
    total_change = (current_price - start_price) / start_price * 100
    
    if total_change > 3:  # 涨3%以上
        change_score = 1
    elif total_change < -3:  # 跌3%以上
        change_score = -1
    else:
        change_score = 0
    
    # 综合得分
    total_score = price_score + low_score + change_score
    
    # 判断
    if total_score >= 2:
        return "bull"
    elif total_score <= -1:
        return "bear"
    else:
        return "neutral"


def test_with_mock_data():
    """用模拟数据测试"""
    
    print("=" * 70)
    print("🧪 市场判断测试 - 综合评分法")
    print("=" * 70)
    
    # 模拟牛市数据（低点不断抬高）
    bull_highs = [100 + i * 2 for i in range(100)]
    bull_lows = [95 + i * 2 for i in range(100)]
    bull_closes = [97 + i * 2 for i in range(100)]
    
    print("\n📈 模拟牛市数据:")
    print(f"   低点变化: {bull_lows[0]} → {bull_lows[-1]}")
    print(f"   价格变化: {bull_closes[0]} → {bull_closes[-1]}")
    
    result_v1 = get_market_type_v1(bull_highs, bull_lows, bull_closes)
    result_v2 = get_market_type_v2(bull_highs, bull_lows, bull_closes)
    
    print(f"   原方法结果: {result_v1}")
    print(f"   新方法结果: {result_v2}")
    
    # 模拟熊市数据（高点不断降低）
    bear_highs = [300 - i * 2 for i in range(100)]
    bear_lows = [290 - i * 2 for i in range(100)]
    bear_closes = [295 - i * 2 for i in range(100)]
    
    print("\n📉 模拟熊市数据:")
    print(f"   高点变化: {bear_highs[0]} → {bear_highs[-1]}")
    print(f"   价格变化: {bear_closes[0]} → {bear_closes[-1]}")
    
    result_v1 = get_market_type_v1(bear_highs, bear_lows, bear_closes)
    result_v2 = get_market_type_v2(bear_highs, bear_lows, bear_closes)
    
    print(f"   原方法结果: {result_v1}")
    print(f"   新方法结果: {result_v2}")
    
    # 模拟震荡数据（无明显趋势）
    neutral_highs = [150 + random.uniform(-10, 10) for _ in range(100)]
    neutral_lows = [140 + random.uniform(-10, 10) for _ in range(100)]
    neutral_closes = [145 + random.uniform(-10, 10) for _ in range(100)]
    
    print("\n📊 模拟震荡数据:")
    print(f"   高点范围: {min(neutral_highs[-60:]):.2f} ~ {max(neutral_highs[-60:]):.2f}")
    print(f"   低点范围: {min(neutral_lows[-60:]):.2f} ~ {max(neutral_lows[-60:]):.2f}")
    
    result_v1 = get_market_type_v1(neutral_highs, neutral_lows, neutral_closes)
    result_v2 = get_market_type_v2(neutral_highs, neutral_lows, neutral_closes)
    
    print(f"   原方法结果: {result_v1}")
    print(f"   新方法结果: {result_v2}")


if __name__ == "__main__":
    test_with_mock_data()
