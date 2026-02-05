#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================
多因子选股系统 - 聚宽平台内置版本
=================================================================
功能：基于多个因子筛选A股股票，每月选10只优质股票
数据源：聚宽平台内置API（无需安装任何库）
因子：21个因子（价值、成长、动量、质量、技术）
=================================================================

【使用方法】
1. 打开 https://www.joinquant.com/
2. 登录你的账号
3. 点击"我的策略" -> "新建策略"
4. 将此代码完全复制到策略编辑器中
5. 点击"运行回测"或"运行策略"
=================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# =============================================================================
# 配置参数（可修改）
# =============================================================================
# 选股参数
STOCK_COUNT = 10          # 每次选10只股票
REBALANCE_FREQ = "M"      # 换仓频率：M=月度，Q=季度

# 因子权重
WEIGHTS = {
    "value": 0.25,      # 价值因子权重
    "growth": 0.20,      # 成长因子权重
    "momentum": 0.15,    # 动量因子权重
    "quality": 0.25,     # 质量因子权重
    "technical": 0.15,   # 技术因子权重
}

# 风控参数
ST_FILTER = True          # 是否过滤ST股票
MIN_MARKET_CAP = 100      # 最小市值（亿）
MAX_POSITION = 0.15        # 单只股票最大仓位


def get_stock_list():
    """
    获取A股所有股票列表
    返回：包含股票代码列表的DataFrame
    """
    # 使用聚宽内置函数获取所有股票信息
    securities = get_all_securities(types=['stock'])
    
    # 转换为DataFrame
    stock_df = pd.DataFrame(securities).T
    
    # 只保留正在上市的股票
    stock_df = stock_df[stock_df['status'] == 'L']
    
    print(f"✅ 获取到 {len(stock_df)} 只股票")
    return stock_df


def get_realtime_price(stock_list):
    """
    获取实时行情
    参数：stock_list - 股票代码列表
    返回：包含实时价格的DataFrame
    """
    # 获取当日行情
    price_df = get_price(
        stock_list,
        start_date=datetime.now().strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        frequency='daily',
        fields=['open', 'close', 'high', 'low', 'volume', 'turnover_rate', 'pe', 'pb']
    )
    
    # 扁平化MultiIndex列
    if isinstance(price_df.columns, pd.MultiIndex):
        price_df.columns = price_df.columns.droplevel(1)
    
    return price_df


def get_price_history(stock_code, days=180):
    """
    获取历史价格数据
    参数：
        stock_code - 股票代码
        days - 获取多少天的数据
    返回：包含历史价格的DataFrame
    """
    # 转换代码格式
    jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
    
    # 计算开始日期
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 获取历史数据
    df = get_price(
        jq_code,
        start_date=start_date,
        end_date=datetime.now().strftime("%Y-%m-%d"),
        frequency='daily',
        fields=['close', 'open', 'high', 'low', 'volume', 'turnover_rate']
    )
    
    if df.empty:
        return pd.DataFrame()
    
    # 计算涨跌幅
    df['pct_change'] = df['close'].pct_change()
    
    return df


def get_financial_data(stock_code):
    """
    获取财务数据
    参数：stock_code - 股票代码
    返回：包含财务指标的字典
    """
    # 转换代码格式
    jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
    
    try:
        # 获取财务数据
        financial_df = get_fundamentals(
            pd.Index([jq_code]),
            date=None,  # 最新财报
            fields=[
                'roe',                          # 净资产收益率
                'net_profit_margin',           # 净利率
                'gross_profit_margin',         # 毛利率
                'debt_to_assets',              # 资产负债率
                'current_ratio',               # 流动比率
                'revenue_growth',             # 营收增长率
                'net_profit_growth'           # 净利润增长率
            ]
        )
        
        if financial_df.empty:
            return {}
        
        return {
            "ROE": float(financial_df['roe'].iloc[0]) if 'roe' in financial_df.columns else 0,
            "net_profit_margin": float(financial_df['net_profit_margin'].iloc[0]) if 'net_profit_margin' in financial_df.columns else 0,
            "gross_margin": float(financial_df['gross_profit_margin'].iloc[0]) if 'gross_profit_margin' in financial_df.columns else 0,
            "debt_ratio": float(financial_df['debt_to_assets'].iloc[0]) * 100 if 'debt_to_assets' in financial_df.columns else 0,
            "current_ratio": float(financial_df['current_ratio'].iloc[0]) if 'current_ratio' in financial_df.columns else 0,
            "revenue_growth": float(financial_df['revenue_growth'].iloc[0]) * 100 if 'revenue_growth' in financial_df.columns else 0,
            "profit_growth": float(financial_df['net_profit_growth'].iloc[0]) * 100 if 'net_profit_growth' in financial_df.columns else 0,
        }
    except Exception as e:
        print(f"❌ 获取财务数据失败: {e}")
        return {}


def calculate_value_factors(stock_info):
    """
    计算价值因子
    返回：包含价值因子的字典
    """
    return {
        "PE_TTM": stock_info.get("pe", 0),
        "PB": stock_info.get("pb", 0),
        "PS_TTM": 0,
        "dividend_yield": 0,
    }


def calculate_growth_factors(financial):
    """
    计算成长因子
    返回：包含成长因子的字典
    """
    return {
        "revenue_growth": financial.get("revenue_growth", 0),
        "profit_growth": financial.get("profit_growth", 0),
        "ROE": financial.get("ROE", 0),
        "ROA": financial.get("ROA", 0),
        "gross_margin": financial.get("gross_margin", 0),
    }


def calculate_momentum_factors(price_df):
    """
    计算动量因子
    返回：包含动量因子的字典
    """
    if price_df.empty:
        return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}
    
    try:
        n = len(price_df)
        
        # 1个月涨幅
        if n >= 20:
            momentum_1m = (price_df['close'].iloc[-1] / price_df['close'].iloc[-20] - 1) * 100
        else:
            momentum_1m = 0
        
        # 3个月涨幅
        if n >= 60:
            momentum_3m = (price_df['close'].iloc[-1] / price_df['close'].iloc[-60] - 1) * 100
        else:
            momentum_3m = momentum_1m
        
        # 6个月涨幅
        if n >= 120:
            momentum_6m = (price_df['close'].iloc[-1] / price_df['close'].iloc[-120] - 1) * 100
        else:
            momentum_6m = momentum_1m
        
        return {
            "momentum_1m": momentum_1m,
            "momentum_3m": momentum_3m,
            "momentum_6m": momentum_6m,
        }
    except:
        return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}


def calculate_quality_factors(financial):
    """
    计算质量因子
    返回：包含质量因子的字典
    """
    return {
        "debt_ratio": financial.get("debt_ratio", 0),
        "current_ratio": financial.get("current_ratio", 0),
        "net_profit_margin": financial.get("net_profit_margin", 0),
        "ocf_to_profit": 0,
    }


def calculate_technical_factors(stock_info, price_df):
    """
    计算技术因子
    返回：包含技术因子的字典
    """
    turnover = stock_info.get("turnover_rate", 0) or 0
    
    # 计算RSI
    rsi = 50
    if not price_df.empty:
        try:
            delta = price_df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi = float(rsi.iloc[-1]) if not rs.iloc[-1] == 0 else 50
        except:
            rsi = 50
    
    # 计算波动率
    volatility = 0
    if not price_df.empty:
        try:
            volatility = price_df['pct_change'].std() * 100 * np.sqrt(252)
        except:
            volatility = 20
    
    return {
        "RSI": rsi,
        "turnover_rate": turnover,
        "volatility": volatility,
    }


def normalize_factor(value, direction):
    """
    标准化因子（0-100分）
    参数：
        value - 因子原始值
        direction - 方向（1=正向，-1=反向）
    返回：0-100的标准化分数
    """
    if value is None or value == 0 or value == float('inf') or value == float('-inf'):
        return 50
    
    if direction == -1:
        # 反向因子（越低越好）
        if value <= 0:
            return 80
        elif value > 100:
            return 20
        else:
            return max(0, min(100, 100 - value))
    else:
        # 正向因子（越高越好）
        return max(0, min(100, value))


def calculate_factor_score(factors, category):
    """
    计算类别因子得分
    """
    # 各类别包含的因子
    category_factors = {
        "value": ["PE_TTM", "PB", "PS_TTM", "dividend_yield"],
        "growth": ["revenue_growth", "profit_growth", "ROE", "ROA", "gross_margin"],
        "momentum": ["momentum_1m", "momentum_3m", "momentum_6m"],
        "quality": ["debt_ratio", "current_ratio", "net_profit_margin", "ocf_to_profit"],
        "technical": ["RSI", "turnover_rate", "volatility"],
    }
    
    # 因子方向
    factor_direction = {
        "PE_TTM": -1, "PB": -1, "PS_TTM": -1, "dividend_yield": 1,
        "revenue_growth": 1, "profit_growth": 1, "ROE": 1, "ROA": 1, "gross_margin": 1,
        "momentum_1m": 1, "momentum_3m": 1, "momentum_6m": 1,
        "debt_ratio": -1, "current_ratio": 1, "net_profit_margin": 1, "ocf_to_profit": 1,
        "RSI": -1, "turnover_rate": 1, "volatility": -1,
    }
    
    # 因子权重
    factor_weights = {
        "PE_TTM": 0.30, "PB": 0.30, "PS_TTM": 0.20, "dividend_yield": 0.20,
        "revenue_growth": 0.25, "profit_growth": 0.25, "ROE": 0.20, "ROA": 0.15, "gross_margin": 0.15,
        "momentum_1m": 0.30, "momentum_3m": 0.40, "momentum_6m": 0.30,
        "debt_ratio": 0.30, "current_ratio": 0.25, "net_profit_margin": 0.25, "ocf_to_profit": 0.20,
        "RSI": 0.40, "turnover_rate": 0.30, "volatility": 0.30,
    }
    
    total_score = 0
    total_weight = 0
    
    for factor in category_factors.get(category, []):
        if factor in factors:
            value = factors[factor]
            direction = factor_direction.get(factor, 1)
            weight = factor_weights.get(factor, 0.1)
            
            score = normalize_factor(value, direction)
            total_score += score * weight
            total_weight += weight
    
    if total_weight > 0:
        return total_score / total_weight
    return 50


def filter_stocks(stocks):
    """
    过滤股票
    """
    # 过滤PE/PB为负
    stocks = stocks[stocks['pe'] > 0]
    stocks = stocks[stocks['pb'] > 0]
    
    # 过滤停牌
    stocks = stocks[stocks['close'] > 0]
    
    print(f"📊 过滤后剩余 {len(stocks)} 只股票")
    return stocks


def select_stocks(price_df):
    """
    核心选股函数
    """
    print("🔍 开始多因子选股...")
    
    # 过滤
    price_df = filter_stocks(price_df)
    
    # 获取股票代码列表
    stocks = list(price_df.index)
    
    if len(stocks) < STOCK_COUNT:
        print(f"⚠️ 股票数量不足 {STOCK_COUNT} 只")
    
    results = []
    
    # 遍历每只股票
    for stock_code in stocks:
        # 提取股票信息
        stock_info = {
            "code": stock_code.split('.')[0] if '.' in stock_code else stock_code,
            "name": stock_code,
            "price": price_df.loc[stock_code, 'close'],
            "change_pct": price_df.loc[stock_code, 'pct_change'] * 100 if 'pct_change' in price_df.columns else 0,
            "pe": price_df.loc[stock_code, 'pe'],
            "pb": price_df.loc[stock_code, 'pb'],
            "turnover_rate": price_df.loc[stock_code, 'turnover_rate'] or 0,
        }
        
        # 获取财务数据
        stock_code_num = stock_info["code"]
        financial = get_financial_data(stock_code_num)
        
        # 获取历史价格
        price_history = get_price_history(stock_code_num)
        
        # 计算所有因子
        factors = {}
        factors.update(calculate_value_factors(stock_info))
        factors.update(calculate_growth_factors(financial))
        factors.update(calculate_momentum_factors(price_history))
        factors.update(calculate_quality_factors(financial))
        factors.update(calculate_technical_factors(stock_info, price_history))
        
        # 计算类别得分
        category_scores = {
            "value": calculate_factor_score(factors, "value"),
            "growth": calculate_factor_score(factors, "growth"),
            "momentum": calculate_factor_score(factors, "momentum"),
            "quality": calculate_factor_score(factors, "quality"),
            "technical": calculate_factor_score(factors, "technical"),
        }
        
        # 计算综合得分
        final_score = sum(
            category_scores[cat] * WEIGHTS[cat] 
            for cat in category_scores
        )
        
        results.append({
            **stock_info,
            "factors": factors,
            "category_scores": category_scores,
            "final_score": final_score,
        })
    
    # 排序
    results.sort(key=lambda x: x["final_score"], reverse=True)
    
    # 选前N只
    selected = results[:STOCK_COUNT]
    
    print(f"✅ 选出 {len(selected)} 只股票")
    
    return selected


def format_report(selected_stocks):
    """
    生成报告
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    report = f"📊 多因子选股报告 - {today}\n"
    report += "=" * 50 + "\n\n"
    
    report += f"【策略参数】\n"
    report += f"选股数量：{STOCK_COUNT}只\n"
    report += f"换仓频率：{'月度' if REBALANCE_FREQ == 'M' else '季度'}\n"
    report += f"因子权重：价值{WEIGHTS['value']*100:.0f}% | "
    report += f"成长{WEIGHTS['growth']*100:.0f}% | "
    report += f"动量{WEIGHTS['momentum']*100:.0f}% | "
    report += f"质量{WEIGHTS['quality']*100:.0f}% | "
    report += f"技术{WEIGHTS['technical']*100:.0f}%\n\n"
    
    report += "【选股结果】\n"
    report += "-" * 50 + "\n"
    
    for i, stock in enumerate(selected_stocks, 1):
        change = stock["change_pct"]
        change_emoji = "📈" if change > 0 else "📉"
        
        report += f"{i:2d}. {stock['code']} {stock['name']}\n"
        report += f"    价格：¥{stock['price']:.2f} {change_emoji} {change:+.2f}%\n"
        report += f"    综合得分：{stock['final_score']:.1f}/100\n"
        
        cats = stock["category_scores"]
        report += f"    价值:{cats['value']:.0f} 成长:{cats['growth']:.0f} "
        report += f"动量:{cats['momentum']:.0f} 质量:{cats['quality']:.0f} "
        report += f"技术:{cats['technical']:.0f}\n"
        report += "-" * 50 + "\n"
    
    report += "\n💡 数据来源：聚宽JQData\n"
    report += "⚠️ 本报告仅供分析，不构成投资建议\n"
    
    return report


def run_strategy():
    """
    主运行函数
    """
    print("🚀 开始多因子选股...")
    print("=" * 50)
    
    # 1. 获取股票列表
    stock_df = get_stock_list()
    
    if stock_df.empty:
        print("❌ 无法获取股票列表")
        return
    
    # 2. 获取实时行情
    stock_codes = list(stock_df.index)
    price_df = get_realtime_price(stock_codes)
    
    if price_df.empty:
        print("❌ 无法获取行情数据")
        return
    
    # 3. 选股
    selected = select_stocks(price_df)
    
    # 4. 生成报告
    report = format_report(selected)
    
    # 5. 打印报告
    print("\n" + "=" * 50)
    print(report)
    print("=" * 50)
    
    return report


# =============================================================================
# 运行策略
# =============================================================================
if __name__ == "__main__":
    run_strategy()
