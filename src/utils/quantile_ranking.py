# -*- coding: utf-8 -*-
"""
分位数排名模块

将因子值转换为排名分数，支持多种排名方式。
"""

import numpy as np
import pandas as pd
from typing import Optional


def quantile_ranking(
    data: pd.Series,
    bins: int = 10,
    ascending: bool = True,
    reverse_score: bool = False,
    min_periods: Optional[int] = None
) -> pd.Series:
    """
    分位数排名：将数据按分位分组并转换为分数

    Args:
        data: 输入数据 Series
        bins: 分位数量（默认10档，对应1-10分）
        ascending: 是否升序排列（True=小值排第一）
        reverse_score: 是否反转分数（对于"越低越好"的指标）
        min_periods: 最少有效样本数

    Returns:
        分数 Series（1-10分）

    Example:
        >>> s = pd.Series([10, 20, 30, 40, 50])
        >>> quantile_ranking(s, bins=5)
        0    1.0
        1    2.0
        2    3.0
        3    4.0
        4    5.0
        dtype: float64
    """
    if data.empty:
        return data
    
    result = data.copy().astype(float)
    
    # 计算分位边界
    percentiles = np.linspace(0, 100, bins + 1)
    limits = [np.nanpercentile(data.dropna(), p) for p in percentiles]
    
    # 避免边界重复值
    for i in range(len(limits) - 1):
        if limits[i] == limits[i + 1]:
            limits[i + 1] += 1e-10
    
    # 使用 pd.qcut 进行分位分组
    try:
        # 计算每个值属于哪个分位
        labels = list(range(1, bins + 1))
        binned = pd.qcut(
            result.rank(method='min'),
            q=bins,
            labels=labels,
            duplicates='drop'
        )
        result = binned.astype(float)
    except ValueError:
        # 如果分位失败，使用 rank 转换为分数
        if ascending:
            ranks = result.rank(method='average', ascending=True)
        else:
            ranks = result.rank(method='average', ascending=False)
        
        # 归一化到 1-bins
        min_rank = ranks.min()
        max_rank = ranks.max()
        if max_rank > min_rank:
            result = ((ranks - min_rank) / (max_rank - min_rank)) * (bins - 1) + 1
        else:
            result = pd.Series(bins / 2, index=data.index)
    
    # 反转分数（对于"越低越好"的指标）
    if reverse_score:
        result = bins + 1 - result
    
    return result


def percentile_ranking(data: pd.Series) -> pd.Series:
    """
    百分位排名：返回每个值的百分位排名（0-100）

    Args:
        data: 输入数据

    Returns:
        百分位排名（0-100）

    Example:
        >>> s = pd.Series([10, 20, 30, 40, 50])
        >>> percentile_ranking(s)
        0      0.0
        1     25.0
        2     50.0
        3     75.0
        4    100.0
    """
    if data.empty:
        return data
    
    ranks = data.rank(method='average', pct=True) * 100
    return ranks


def rank_percentile(
    data: pd.Series,
    top_pct: float = 10.0,
    ascending: bool = False
) -> pd.Series:
    """
    判断是否在 top X%

    Args:
        data: 输入数据
        top_pct: top 百分比（默认10%）
        ascending: 升序还是降序

    Returns:
        Boolean Series（True=在top X%）
    """
    if data.empty:
        return data
    
    pct = data.rank(method='average', pct=True)
    
    if ascending:
        # 升序：值越大越靠前
        return pct >= (100 - top_pct) / 100
    else:
        # 降序：值越小越靠前
        return pct <= top_pct / 100


def z_score(data: pd.Series) -> pd.Series:
    """
    Z-Score 标准化

    Args:
        data: 输入数据

    Returns:
        Z-Score 值

    Example:
        >>> s = pd.Series([10, 20, 30, 40, 50])
        >>> z_score(s)
        0   -1.41
        1   -0.71
        2    0.00
        3    0.71
        4    1.41
    """
    if data.empty:
        return data
    
    mean = data.mean()
    std = data.std()
    
    if std == 0:
        return pd.Series(0, index=data.index)
    
    return (data - mean) / std


def rank_to_score(
    data: pd.Series,
    bins: int = 10,
    higher_is_better: bool = True
) -> pd.Series:
    """
    排名转分数（便捷函数）

    Args:
        data: 输入数据
        bins: 分档数量
        higher_is_better: True=值越大分数越高

    Returns:
        分数（1-bins）
    """
    if data.empty:
        return data
    
    if higher_is_better:
        return quantile_ranking(data, bins=bins, ascending=True)
    else:
        return quantile_ranking(data, bins=bins, ascending=True, reverse_score=True)


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("分位数排名模块测试")
    print("=" * 60)
    
    # 测试数据
    test_data = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    
    print("\n原始数据:")
    print(test_data.values)
    
    print("\n10档排名（越高越好）:")
    result = rank_to_score(test_data, bins=10, higher_is_better=True)
    print(result.values)
    
    print("\n10档排名（越低越好）:")
    result2 = rank_to_score(test_data, bins=10, higher_is_better=False)
    print(result2.values)
    
    print("\n百分位排名:")
    pct = percentile_ranking(test_data)
    print(pct.values)
    
    print("\nZ-Score:")
    z = z_score(test_data)
    print(z.values)
    
    print("\nTop 20% 标记:")
    top = rank_percentile(test_data, top_pct=20)
    print(top.values)
    
    print("\n" + "=" * 60)
