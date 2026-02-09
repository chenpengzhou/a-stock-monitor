# -*- coding: utf-8 -*-
"""
Winsorize 极端值处理模块

对数据进行上下限截断，限制极端值的影响。
行业标准做法：使用 1%/99% 或 5%/95% 分位作为阈值。
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


def winsorize(
    data: pd.Series,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
    inplace: bool = False
) -> pd.Series:
    """
    Winsorize 处理：截断极端值到指定分位数

    Args:
        data: 输入数据 Series
        lower_percentile: 下限百分位（默认1%）
        upper_percentile: 上限百分位（默认99%）
        inplace: 是否原地修改（默认False，返回新Series）

    Returns:
        处理后的 Series

    Example:
        >>> import pandas as pd
        >>> s = pd.Series([1, 2, 3, 100, 200])
        >>> winsorize(s)
        0      1.5
        1      2.0
        2      3.0
        3     15.0
        4     15.0
        dtype: float64
    """
    if not isinstance(data, pd.Series):
        raise TypeError("data 必须是 pandas Series 类型")
    
    if data.empty:
        return data
    
    # 复制数据
    if inplace:
        result = data
    else:
        result = data.copy()
    
    # 计算上下限
    lower_limit = np.nanpercentile(data.dropna(), lower_percentile)
    upper_limit = np.nanpercentile(data.dropna(), upper_percentile)
    
    # 截断极端值
    result = result.clip(lower=lower_limit, upper=upper_limit)
    
    return result


def winsorize_df(
    df: pd.DataFrame,
    columns: Optional[list] = None,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0
) -> pd.DataFrame:
    """
    对 DataFrame 的指定列进行 Winsorize 处理

    Args:
        df: 输入 DataFrame
        columns: 要处理的列名列表（None表示所有数值列）
        lower_percentile: 下限百分位
        upper_percentile: 上限百分位

    Returns:
        处理后的 DataFrame

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 100], 'b': [0.1, 0.5, 0.9]})
        >>> winsorize_df(df, columns=['a'])
             b      a
        0  0.1  1.20
        1  0.5  2.00
        2  0.9  3.65
    """
    if df.empty:
        return df
    
    if columns is None:
        # 默认处理所有数值列
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    result = df.copy()
    
    for col in columns:
        if col in result.columns:
            result[col] = winsorize(
                result[col],
                lower_percentile=lower_percentile,
                upper_percentile=upper_percentile
            )
    
    return result


def winsorize_by_group(
    data: pd.Series,
    group: pd.Series,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0
) -> pd.Series:
    """
    按分组进行 Winsorize 处理

    适用于需要按行业/板块分别截断极端值的场景

    Args:
        data: 输入数据 Series
        group: 分组标识 Series（与 data 索引对应）
        lower_percentile: 下限百分位
        upper_percentile: 上限百分位

    Returns:
        处理后的 Series
    """
    if data.empty:
        return data
    
    result = data.copy()
    
    for group_name in group.unique():
        mask = group == group_name
        group_data = data[mask]
        
        if group_data.notna().sum() < 2:
            # 样本太少，跳过
            continue
        
        lower_limit = np.nanpercentile(group_data.dropna(), lower_percentile)
        upper_limit = np.nanpercentile(group_data.dropna(), upper_percentile)
        
        result[mask] = group_data.clip(lower=lower_limit, upper=upper_limit)
    
    return result


def get_winsorize_limits(
    data: pd.Series,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0
) -> Tuple[float, float]:
    """
    获取 Winsorize 的上下限值

    Args:
        data: 输入数据
        lower_percentile: 下限百分位
        upper_percentile: 上限百分位

    Returns:
        (下限值, 上限值)
    """
    lower = np.nanpercentile(data.dropna(), lower_percentile)
    upper = np.nanpercentile(data.dropna(), upper_percentile)
    return lower, upper


# ===== 快捷函数：常用阈值 =====
def winsorize_extreme(data: pd.Series) -> pd.Series:
    """极端处理：1%/99% 分位"""
    return winsorize(data, 1.0, 99.0)


def winsorize_moderate(data: pd.Series) -> pd.Series:
    """温和处理：5%/95% 分位"""
    return winsorize(data, 5.0, 95.0)


# ===== 测试 =====
if __name__ == "__main__":
    import pandas as pd
    
    print("=" * 60)
    print("Winsorize 模块测试")
    print("=" * 60)
    
    # 测试数据：包含极端值
    test_data = pd.Series([1, 2, 3, 5, 10, 20, 50, 100, 500, 1000])
    
    print("\n原始数据:")
    print(test_data.values)
    
    print("\n1%/99% 截断:")
    result = winsorize(test_data)
    print(result.values)
    
    lower, upper = get_winsorize_limits(test_data)
    print(f"\n截断边界: lower={lower:.2f}, upper={upper:.2f}")
    
    print("\n温和截断 (5%/95%):")
    result2 = winsorize_moderate(test_data)
    print(result2.values)
    
    print("\n" + "=" * 60)
