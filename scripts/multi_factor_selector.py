#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统
=================================================================
功能：基于多个因子筛选A股股票，每月选10只优质股票
数据源：AkShare（免费开源A股数据，无需注册）
因子：21个因子（价值、成长、动量、质量、技术）
推送：Telegram
=================================================================
"""

# 导入必要的模块
import sys              # 系统相关功能
import os               # 操作系统功能
import json             # JSON数据处理
import logging          # 日志记录
import subprocess       # 调用外部命令
from datetime import datetime  # 日期时间处理
from pathlib import Path       # 路径处理
from typing import Dict, List, Optional  # 类型提示
import numpy as np      # 数值计算
import pandas as pd     # 数据分析表格

# =============================================================================
# 配置日志格式：时间 - 日志级别 - 消息内容
# =============================================================================
logging.basicConfig(
    level=logging.INFO,  # 日志级别设为INFO
    format='%(asctime)s - %(levelname)s - %(message)s'  # 日志格式
)
logger = logging.getLogger(__name__)  # 创建日志对象

# =============================================================================
# 定义路径常量
# PROJECT_PATH: 当前脚本所在目录
# CONFIG_PATH: 配置文件目录
# DATA_PATH: 数据文件目录
# LOGS_PATH: 日志文件目录
# =============================================================================
PROJECT_PATH = Path(__file__).parent      # 获取当前脚本的父目录
CONFIG_PATH = PROJECT_PATH / "config"     # 配置目录
DATA_PATH = PROJECT_PATH / "data"         # 数据目录
LOGS_PATH = PROJECT_PATH / "logs"         # 日志目录

# 确保所有目录存在，如果不存在则创建
CONFIG_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class MultiFactorStockSelector:
    """
    多因子选股器类
    用于基于多个因子筛选A股优质股票
    """
    
    def __init__(self):
        """
        初始化选股器
        设置选股参数、因子权重、过滤条件等
        """
        
        # ------------------------------------------------------------------
        # 策略配置参数
        # ------------------------------------------------------------------
        self.config = {
            # 因子权重（可调，建议根据回测调整）
            # 价值因子占25%，成长因子占20%，动量因子占15%，
            # 质量因子占25%，技术因子占15%
            "weights": {
                "value": 0.25,      # 价值因子权重
                "growth": 0.20,      # 成长因子权重
                "momentum": 0.15,    # 动量因子权重
                "quality": 0.25,     # 质量因子权重
                "technical": 0.15,   # 技术因子权重
            },
            
            # 选股参数
            "stock_count": 10,       # 每次选10只股票
            "rebalance_freq": "M",   # 换仓频率：M=月度，Q=季度
            
            # 风控参数
            "max_position": 0.15,    # 单只股票最大仓位15%
            "min_market_cap": 100,   # 最小市值100亿
            
            # 过滤条件
            "excluded_industries": ["银行", "房地产", "保险"],  # 排除的行业
            "st_filter": True,       # 是否过滤ST股票
            "new_stock_filter": True,  # 是否过滤次新股（上市不满6个月）
        }
        
        # ------------------------------------------------------------------
        # 因子方向配置
        # 1表示正向（越高越好），-1表示反向（越低越好）
        # ------------------------------------------------------------------
        self.factor_direction = {
            # ---------------------- 价值因子（越低越好） ----------------------
            "PE_TTM": -1,           # 市盈率越低越好
            "PB": -1,               # 市净率越低越好
            "PS_TTM": -1,           # 市销率越低越好
            "dividend_yield": 1,    # 股息率越高越好
            
            # ---------------------- 成长因子（越高越好） ----------------------
            "revenue_growth": 1,    # 营收增速越高越好
            "profit_growth": 1,     # 利润增速越高越好
            "ROE": 1,               # 净资产收益率越高越好
            "ROA": 1,               # 资产收益率越高越好
            "gross_margin": 1,       # 毛利率越高越好
            
            # ---------------------- 动量因子（越高越好） ----------------------
            "momentum_1m": 1,       # 近1月涨幅越高越好
            "momentum_3m": 1,       # 近3月涨幅越高越好
            "momentum_6m": 1,       # 近6月涨幅越高越好
            
            # ---------------------- 质量因子 ----------------------
            "debt_ratio": -1,       # 资产负债率越低越好
            "current_ratio": 1,     # 流动比率越高越好
            "net_profit_margin": 1, # 净利润率越高越好
            "ocf_to_profit": 1,     # 经营现金流/净利润越高越好
            
            # ---------------------- 技术因子 ----------------------
            "RSI": -1,             # RSI偏低表示超卖，更好
            "turnover_rate": 1,     # 换手率适中
            "volatility": -1,       # 波动率越低越好
        }
        
        # ------------------------------------------------------------------
        # 各因子在类别内的权重
        # 例如：价值因子中，PE_TTM占30%，PB占30%
        # ------------------------------------------------------------------
        self.factor_weights = {
            # 价值因子内部权重
            "PE_TTM": 0.30,         # 市盈率占价值因子的30%
            "PB": 0.30,             # 市净率占价值因子的30%
            "PS_TTM": 0.20,         # 市销率占价值因子的20%
            "dividend_yield": 0.20, # 股息率占价值因子的20%
            
            # 成长因子内部权重
            "revenue_growth": 0.25, # 营收增速占25%
            "profit_growth": 0.25,   # 利润增速占25%
            "ROE": 0.20,            # ROE占20%
            "ROA": 0.15,            # ROA占15%
            "gross_margin": 0.15,    # 毛利率占15%
            
            # 动量因子内部权重
            "momentum_1m": 0.30,    # 1月涨幅占30%
            "momentum_3m": 0.40,    # 3月涨幅占40%（最重要）
            "momentum_6m": 0.30,    # 6月涨幅占30%
            
            # 质量因子内部权重
            "debt_ratio": 0.30,     # 资产负债率占30%
            "current_ratio": 0.25,   # 流动比率占25%
            "net_profit_margin": 0.25, # 净利润率占25%
            "ocf_to_profit": 0.20,   # 现金流占20%
            
            # 技术因子内部权重
            "RSI": 0.40,            # RSI占40%（最重要）
            "turnover_rate": 0.30,   # 换手率占30%
            "volatility": 0.30,      # 波动率占30%
        }
        
        # 用于存储股票数据
        self.stock_data = {}
    
    def import_akshare(self):
        """
        导入AkShare库
        返回akshare模块，如果导入失败返回None
        """
        try:
            import akshare as ak  # 尝试导入akshare
            return ak             # 导入成功，返回模块
        except ImportError:       # 如果导入失败
            logger.error("AkShare未安装，请运行: pip install akshare")
            return None           # 返回None
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股实时行情数据
        返回：包含所有A股实时行情的DataFrame
        """
        import akshare as ak  # 导入akshare
        
        logger.info("📥 获取A股行情数据...")  # 记录日志
        
        try:
            # stock_zh_a_spot_em() 是东方财富的实时行情接口
            # 返回所有A股的代码、名称、价格、涨跌幅等信息
            stock_df = ak.stock_zh_a_spot_em()
            
            logger.info(f"✅ 获取到 {len(stock_df)} 只股票")  # 记录获取到的股票数量
            return stock_df  # 返回数据
            
        except Exception as e:  # 如果出错
            logger.error(f"❌ 获取行情失败: {e}")  # 记录错误日志
            return pd.DataFrame()  # 返回空表格
    
    def get_financial_data(self, stock_code: str) -> Dict:
        """
        获取单只股票的财务数据
        参数：stock_code - 股票代码，如'000001'
        返回：包含财务指标的字典
        """
        import akshare as ak  # 导入akshare
        
        try:
            # stock_financial_analysis_indicator() 获取财务分析指标
            # 返回ROE、毛利率、资产负债率等财务数据
            financial_df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            # 如果数据为空，返回空字典
            if financial_df.empty:
                return {}
            
            # 获取最新一期的财务数据（第一行）
            latest = financial_df.iloc[0]
            
            # 提取需要的财务指标，转换为float类型
            return {
                "ROE": float(latest.get("净资产收益率(%)", 0) or 0),      # 净资产收益率
                "ROA": float(latest.get("资产报酬率(%)", 0) or 0),         # 资产报酬率
                "gross_margin": float(latest.get("毛利率(%)", 0) or 0),     # 毛利率
                "net_profit_margin": float(latest.get("净利率(%)", 0) or 0), # 净利率
                "debt_ratio": float(latest.get("资产负债率(%)", 0) or 0),    # 资产负债率
                "revenue_growth": float(latest.get("营业收入增长率(%)", 0) or 0),  # 营收增速
                "profit_growth": float(latest.get("净利润增长率(%)", 0) or 0),     # 利润增速
            }
            
        except Exception as e:  # 如果出错
            return {}  # 返回空字典
    
    def get_price_history(self, stock_code: str, days: int = 180) -> pd.DataFrame:
        """
        获取股票历史价格数据
        参数：
            stock_code - 股票代码
            days - 获取多少天的数据，默认180天
        返回：包含历史价格的DataFrame
        """
        import akshare as ak  # 导入akshare
        
        try:
            # 转换为akshare需要的代码格式
            # 沪市以6开头，转换为XSHG（上海交易所）
            # 深市以0或3开头，转换为SZSE（深圳交易所）
            jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
            
            # stock_zh_a_hist() 获取A股历史K线数据
            # period="daily" 表示日线
            # start_date="20250101" 表示从2025年1月1日开始
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date="20250101")
            
            # 如果数据为空，返回空表格
            if df.empty:
                return pd.DataFrame()
            
            # 按日期排序（从早到晚）
            df = df.sort_values('日期')
            
            # 计算每日涨跌幅
            df['pct_change'] = df['收盘'].pct_change()
            
            return df
            
        except Exception as e:  # 如果出错
            return pd.DataFrame()  # 返回空表格
    
    def calculate_value_factors(self, stock: Dict) -> Dict:
        """
        计算价值因子
        价值因子衡量股票的估值水平
        返回：包含价值因子的字典
        """
        return {
            "PE_TTM": stock.get("pe", 0),              # 市盈率
            "PB": stock.get("pb", 0),                  # 市净率
            "PS_TTM": 0,                                # 市销率（AkShare暂无）
            "dividend_yield": stock.get("dividend_yield", 0),  # 股息率
        }
    
    def calculate_growth_factors(self, financial: Dict) -> Dict:
        """
        计算成长因子
        成长因子衡量公司的业绩增长能力
        返回：包含成长因子的字典
        """
        return {
            "revenue_growth": financial.get("revenue_growth", 0),  # 营收增长率
            "profit_growth": financial.get("profit_growth", 0),    # 利润增长率
            "ROE": financial.get("ROE", 0),                      # 净资产收益率
            "ROA": financial.get("ROA", 0),                      # 资产收益率
            "gross_margin": financial.get("gross_margin", 0),      # 毛利率
        }
    
    def calculate_momentum_factors(self, price_df: pd.DataFrame) -> Dict:
        """
        计算动量因子
        动量因子衡量股票的价格趋势强度
        返回：包含动量因子的字典
        """
        # 如果没有价格数据，返回0
        if price_df.empty:
            return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}
        
        try:
            n = len(price_df)  # 获取数据行数
            
            # 计算1个月涨幅（约20个交易日）
            if n >= 20:
                # 用最新收盘价 / 20天前收盘价 - 1 = 涨跌幅
                momentum_1m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-20] - 1) * 100
            else:
                momentum_1m = 0  # 数据不足1个月
            
            # 计算3个月涨幅（约60个交易日）
            if n >= 60:
                momentum_3m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-60] - 1) * 100
            else:
                momentum_3m = momentum_1m  # 数据不足3个月，用1个月代替
            
            # 计算6个月涨幅（约120个交易日）
            if n >= 120:
                momentum_6m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-120] - 1) * 100
            else:
                momentum_6m = momentum_1m  # 数据不足6个月，用1个月代替
            
            return {
                "momentum_1m": momentum_1m,  # 1个月涨幅
                "momentum_3m": momentum_3m,  # 3个月涨幅
                "momentum_6m": momentum_6m,  # 6个月涨幅
            }
        except:  # 如果计算出错
            return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}
    
    def calculate_quality_factors(self, financial: Dict) -> Dict:
        """
        计算质量因子
        质量因子衡量公司的财务健康度
        返回：包含质量因子的字典
        """
        return {
            "debt_ratio": financial.get("debt_ratio", 0),            # 资产负债率
            "current_ratio": financial.get("current_ratio", 0),      # 流动比率
            "net_profit_margin": financial.get("net_profit_margin", 0),  # 净利润率
            "ocf_to_profit": 0,                                      # 经营现金流/净利润（需要现金流数据）
        }
    
    def calculate_technical_factors(self, stock: Dict, price_df: pd.DataFrame) -> Dict:
        """
        计算技术因子
        技术因子基于价格和成交量计算
        返回：包含技术因子的字典
        """
        # 从stock字典中获取换手率
        turnover = stock.get("turnover_rate", 0) or 0
        
        # RSI默认值50（中性）
        rsi = 50
        
        # 如果有价格数据，计算RSI
        if not price_df.empty:
            try:
                # RSI计算公式：
                # delta = 今日收盘价 - 昨日收盘价
                delta = price_df['收盘'].diff()
                
                # gain = 上涨日的平均涨幅（14日）
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                
                # loss = 下跌日的平均跌幅（14日）
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                
                # RS = gain / loss
                rs = gain / loss
                
                # RSI = 100 - 100 / (1 + RS)
                rsi = 100 - (100 / (1 + rs))
                
                # 取最新的RSI值
                rsi = float(rsi.iloc[-1]) if not rs.iloc[-1] == 0 else 50
            except:
                rsi = 50  # 计算失败用默认值
        
        # 计算波动率（年化）
        volatility = 0
        if not price_df.empty:
            try:
                # 日收益率的标准差
                daily_vol = price_df['pct_change'].std()
                
                # 年化波动率 = 日波动率 * sqrt(252) * 100
                volatility = daily_vol * 100 * np.sqrt(252)
            except:
                volatility = 20  # 计算失败用默认值
        
        return {
            "RSI": rsi,              # 相对强弱指数
            "turnover_rate": turnover,  # 换手率
            "volatility": volatility,   # 年化波动率
        }
    
    def normalize_factor(self, value: float, direction: int) -> float:
        """
        标准化因子（将因子值转换为0-100的分数）
        参数：
            value - 因子原始值
            direction - 因子方向（1=正向，-1=反向）
        返回：0-100的标准化分数
        """
        # 处理无效值
        if value is None or value == 0 or value == float('inf') or value == float('-inf'):
            return 50  # 无效值返回中性分数
        
        if direction == -1:
            # 反向因子（越低越好）
            if value <= 0:  # 负值通常表示亏损或特殊情况
                return 80  # 低估值给高分
            elif value > 100:  # 过高估值
                return 20  # 高估值给低分
            else:
                # 线性转换：value越大，分数越低
                return max(0, min(100, 100 - value))
        else:
            # 正向因子（越高越好）
            # 线性映射到0-100范围
            return max(0, min(100, value))
    
    def calculate_factor_score(self, factors: Dict, category: str) -> float:
        """
        计算某一类别的因子得分
        参数：
            factors - 包含所有因子值的字典
            category - 因子类别（value/growth/momentum/quality/technical）
        返回：类别综合得分（0-100）
        """
        # 定义各类别包含的因子
        category_factors = {
            "value": ["PE_TTM", "PB", "PS_TTM", "dividend_yield"],
            "growth": ["revenue_growth", "profit_growth", "ROE", "ROA", "gross_margin"],
            "momentum": ["momentum_1m", "momentum_3m", "momentum_6m"],
            "quality": ["debt_ratio", "current_ratio", "net_profit_margin", "ocf_to_profit"],
            "technical": ["RSI", "turnover_rate", "volatility"],
        }
        
        total_score = 0    # 加权总分
        total_weight = 0   # 权重总和
        
        # 遍历该类别下的所有因子
        for factor in category_factors.get(category, []):
            if factor in factors:  # 如果因子存在
                value = factors[factor]  # 获取因子值
                direction = self.factor_direction.get(factor, 1)  # 获取因子方向
                weight = self.factor_weights.get(factor, 0.1)  # 获取因子权重
                
                # 计算标准化得分
                score = self.normalize_factor(value, direction)
                
                # 累加加权得分
                total_score += score * weight
                total_weight += weight
        
        # 计算平均得分
        if total_weight > 0:
            return total_score / total_weight
        return 50  # 如果没有因子，返回中性分数
    
    def filter_stocks(self, stocks: pd.DataFrame) -> pd.DataFrame:
        """
        过滤股票
        根据设定的条件过滤掉不符合要求的股票
        参数：stocks - 原始股票数据DataFrame
        返回：过滤后的股票DataFrame
        """
        filtered = stocks.copy()  # 复制一份，避免修改原数据
        
        # 过滤ST股票
        if self.config["st_filter"]:
            # ~表示取反，筛选名称中不包含'ST'的股票
            filtered = filtered[~filtered['名称'].str.contains('ST', na=False)]
        
        # 过滤负PE（亏损公司）
        filtered = filtered[filtered['市盈率-动态'] > 0]
        
        # 过滤负PB
        filtered = filtered[filtered['市净率'] > 0]
        
        # 过滤停牌股票（价格为0）
        filtered = filtered[filtered['最新价'] > 0]
        
        logger.info(f"📊 过滤后剩余 {len(filtered)} 只股票")
        return filtered
    
    def select_stocks(self, stocks: pd.DataFrame) -> List[Dict]:
        """
        核心选股函数
        根据多因子模型筛选股票
        参数：stocks - 过滤后的股票DataFrame
        返回：选中的股票列表（按得分降序排列）
        """
        logger.info("🔍 开始多因子选股...")
        
        # 过滤股票
        stocks = self.filter_stocks(stocks)
        
        # 如果股票数量不足10只，使用全部股票
        if len(stocks) < self.config["stock_count"]:
            logger.warning(f"⚠️ 股票数量不足 {self.config['stock_count']} 只，使用全部 {len(stocks)} 只")
        
        results = []  # 存储选股结果
        
        # 遍历每只股票
        for idx, row in stocks.iterrows():
            stock_code = row['代码']     # 获取股票代码
            stock_name = row['名称']     # 获取股票名称
            
            # 提取股票基本信息
            stock_info = {
                "code": stock_code,                                      # 代码
                "name": stock_name,                                      # 名称
                "price": row['最新价'],                                  # 最新价
                "change_pct": row['涨跌幅'],                             # 涨跌幅
                "pe": row['市盈率-动态'],                                # 市盈率
                "pb": row['市净率'],                                     # 市净率
                "turnover_rate": row['换手率'],                          # 换手率
            }
            
            # 获取财务数据
            try:
                financial = self.get_financial_data(stock_code)
            except:
                financial = {}
            
            # 获取历史价格数据
            try:
                price_df = self.get_price_history(stock_code)
            except:
                price_df = pd.DataFrame()
            
            # 计算所有因子
            factors = {}  # 存储所有因子值
            
            # 计算价值因子
            factors.update(self.calculate_value_factors(stock_info))
            
            # 计算成长因子
            factors.update(self.calculate_growth_factors(financial))
            
            # 计算动量因子
            factors.update(self.calculate_momentum_factors(price_df))
            
            # 计算质量因子
            factors.update(self.calculate_quality_factors(financial))
            
            # 计算技术因子
            factors.update(self.calculate_technical_factors(stock_info, price_df))
            
            # 计算各类别得分
            category_scores = {
                "value": self.calculate_factor_score(factors, "value"),      # 价值得分
                "growth": self.calculate_factor_score(factors, "growth"),    # 成长得分
                "momentum": self.calculate_factor_score(factors, "momentum"),  # 动量得分
                "quality": self.calculate_factor_score(factors, "quality"),    # 质量得分
                "technical": self.calculate_factor_score(factors, "technical"),  # 技术得分
            }
            
            # 计算综合得分（各类别加权求和）
            final_score = sum(
                category_scores[cat] * self.config["weights"][cat] 
                for cat in category_scores
            )
            
            # 将结果存入列表
            results.append({
                **stock_info,                 # 股票基本信息
                "factors": factors,            # 所有因子值
                "category_scores": category_scores,  # 各类别得分
                "final_score": final_score,    # 综合得分
            })
        
        # 按综合得分降序排序（得分高的在前）
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 选取前N只股票
        selected = results[:self.config["stock_count"]]
        
        logger.info(f"✅ 选出 {len(selected)} 只股票")
        
        return selected
    
    def format_report(self, selected_stocks: List[Dict]) -> str:
        """
        生成格式化的选股报告
        参数：selected_stocks - 选中的股票列表
        返回：格式化的报告字符串
        """
        today = datetime.now().strftime("%Y-%m-%d")  # 获取当前日期
        
        # 初始化报告字符串
        report = f"📊 多因子选股报告 - {today}\n"
        report += "=" * 50 + "\n\n"
        
        # 添加策略参数
        report += f"【策略参数】\n"
        report += f"选股数量：{self.config['stock_count']}只\n"
        report += f"换仓频率：{'月度' if self.config['rebalance_freq'] == 'M' else '季度'}\n"
        report += f"因子权重：价值{self.config['weights']['value']*100:.0f}% | "
        report += f"成长{self.config['weights']['growth']*100:.0f}% | "
        report += f"动量{self.config['weights']['momentum']*100:.0f}% | "
        report += f"质量{self.config['weights']['quality']*100:.0f}% | "
        report += f"技术{self.config['weights']['technical']*100:.0f}%\n\n"
        
        # 添加选股结果
        report += "【选股结果】\n"
        report += "-" * 50 + "\n"
        
        # 遍历每只选中的股票
        for i, stock in enumerate(selected_stocks, 1):
            name = stock["name"][:8] if len(stock["name"]) > 8 else stock["name"]
            change = stock["change_pct"]
            change_emoji = "📈" if change > 0 else "📉"
            
            report += f"{i:2d}. {stock['code']} {name}\n"  # 排名、代码、名称
            report += f"    价格：¥{stock['price']:.2f} {change_emoji} {change:+.2f}%\n"
            report += f"    综合得分：{stock['final_score']:.1f}/100\n"
            
            # 添加各类别得分
            cats = stock["category_scores"]
            report += f"    价值:{cats['value']:.0f} 成长:{cats['growth']:.0f} "
            report += f"动量:{cats['momentum']:.0f} 质量:{cats['quality']:.0f} "
            report += f"技术:{cats['technical']:.0f}\n"
            
            # 添加关键因子值
            report += f"    PE:{stock['factors'].get('PE_TTM', 'N/A'):.1f} "
            report += f"ROE:{stock['factors'].get('ROE', 'N/A'):.1f}% "
            report += f"营收增:{stock['factors'].get('revenue_growth', 'N/A'):.1f}%\n"
            report += "-" * 50 + "\n"
        
        # 添加因子说明
        report += "\n【因子说明】\n"
        report += "价值(PE/PB)：估值越低越好\n"
        report += "成长(ROE/营收)：业绩增长越高越好\n"
        report += "动量(涨幅)：趋势延续性\n"
        report += "质量(负债率)：财务健康度\n"
        report += "技术(RSI/换手)：短期表现\n"
        
        # 添加提示
        report += "\n💡 数据来源：AkShare\n"
        report += "⚠️ 本报告仅供分析，不构成投资建议\n"
        
        return report
    
    def save_report(self, report: str):
        """
        保存报告到文件
        参数：report - 报告字符串
        """
        today = datetime.now().strftime("%Y-%m-%d")  # 获取日期
        report_file = DATA_PATH / f"stock_report_{today}.txt"  # 文件路径
        
        with open(report_file, "w", encoding="utf-8") as f:  # 打开文件
            f.write(report)  # 写入报告内容
        
        logger.info(f"📁 报告已保存: {report_file}")  # 记录日志
    
    def send_to_telegram(self, report: str) -> bool:
        """
        发送报告到Telegram
        参数：report - 报告字符串
        返回：是否发送成功
        """
        logger.info("📤 发送到Telegram...")
        
        # 构建命令
        cmd = [
            "openclaw",                     # 调用openclaw命令
            "message",                      # 发送消息
            "send",                         # 发送子命令
            "--channel", "telegram",       # 指定telegram渠道
            "--target", "8303320872",       # 发送给用户ID
            "--message", report             # 消息内容
        ]
        
        try:
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:  # 如果返回码为0，表示成功
                logger.info("✅ 报告已发送到Telegram")
                return True
            else:  # 如果失败
                logger.error(f"❌ 发送失败: {result.stderr}")
                return False
                
        except Exception as e:  # 如果异常
            logger.error(f"❌ 发送异常: {e}")
            return False
    
    def run(self):
        """
        主运行函数
        执行完整的选股流程
        """
        logger.info("🚀 开始多因子选股...")
        
        # 1. 获取股票列表
        stocks = self.get_stock_list()
        
        if stocks.empty:  # 如果获取失败
            logger.error("❌ 无法获取股票数据")
            return None
        
        # 2. 选股
        selected = self.select_stocks(stocks)
        
        # 3. 生成报告
        report = self.format_report(selected)
        
        # 4. 保存报告
        self.save_report(report)
        
        # 5. 发送到Telegram
        self.send_to_telegram(report)
        
        logger.info("✨ 选股完成")
        
        return report


def main():
    """
    主入口函数
    """
    # 创建选股器实例
    selector = MultiFactorStockSelector()
    
    # 执行选股
    report = selector.run()
    
    # 如果成功，打印报告
    if report:
        print("\n" + "=" * 50)
        print(report)
        print("=" * 50)


if __name__ == "__main__":
    # 如果直接运行此脚本
    main()  # 调用主入口
