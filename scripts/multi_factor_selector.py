#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================
多因子选股系统 - 聚宽(JQData)版本
=================================================================
功能：基于多个因子筛选A股股票，每月选10只优质股票
数据源：聚宽JQData（需要账号和API权限）
因子：21个因子（价值、成长、动量、质量、技术）
=================================================================
"""

import sys
import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

# =============================================================================
# 配置日志
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_PATH = Path(__file__).parent
CONFIG_PATH = PROJECT_PATH / "config"
DATA_PATH = PROJECT_PATH / "data"
LOGS_PATH = PROJECT_PATH / "logs"

CONFIG_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 配置聚宽账号（请修改为你的账号）
# =============================================================================
# 在聚宽官网注册后，获取账号密码
# 登录地址：https://www.joinquant.com/
JQ_USERNAME = "13675856229"  # 聚宽用户名（手机号或邮箱）
JQ_PASSWORD = "B9*2Une$A1UqAQ0v"  # 聚宽密码


class MultiFactorStockSelector:
    """
    多因子选股器类 - 聚宽版本
    """
    
    def __init__(self):
        """
        初始化选股器
        """
        # 导入聚宽SDK
        try:
            from jqdatasdk import auth
            self.jq = {"auth": auth}
        except ImportError:
            logger.error("聚宽SDK未安装，请运行: pip install jqdatasdk")
            self.jq = None
        
        # 策略配置参数
        self.config = {
            # 因子权重
            "weights": {
                "value": 0.25,
                "growth": 0.20,
                "momentum": 0.15,
                "quality": 0.25,
                "technical": 0.15,
            },
            
            # 选股参数
            "stock_count": 10,
            "rebalance_freq": "M",
            
            # 风控参数
            "max_position": 0.15,
            "min_market_cap": 100,
            
            # 过滤条件
            "excluded_industries": ["银行", "房地产", "保险"],
            "st_filter": True,
            "new_stock_filter": True,
        }
        
        # 因子方向：1=正向(越高越好)，-1=反向(越低越好)
        self.factor_direction = {
            # 价值因子（越低越好）
            "PE_TTM": -1,
            "PB": -1,
            "PS_TTM": -1,
            "dividend_yield": 1,
            
            # 成长因子（越高越好）
            "revenue_growth": 1,
            "profit_growth": 1,
            "ROE": 1,
            "ROA": 1,
            "gross_margin": 1,
            
            # 动量因子（越高越好）
            "momentum_1m": 1,
            "momentum_3m": 1,
            "momentum_6m": 1,
            
            # 质量因子
            "debt_ratio": -1,
            "current_ratio": 1,
            "net_profit_margin": 1,
            "ocf_to_profit": 1,
            
            # 技术因子
            "RSI": -1,
            "turnover_rate": 1,
            "volatility": -1,
        }
        
        # 因子权重
        self.factor_weights = {
            "PE_TTM": 0.30,
            "PB": 0.30,
            "PS_TTM": 0.20,
            "dividend_yield": 0.20,
            
            "revenue_growth": 0.25,
            "profit_growth": 0.25,
            "ROE": 0.20,
            "ROA": 0.15,
            "gross_margin": 0.15,
            
            "momentum_1m": 0.30,
            "momentum_3m": 0.40,
            "momentum_6m": 0.30,
            
            "debt_ratio": 0.30,
            "current_ratio": 0.25,
            "net_profit_margin": 0.25,
            "ocf_to_profit": 0.20,
            
            "RSI": 0.40,
            "turnover_rate": 0.30,
            "volatility": 0.30,
        }
    
    def login(self) -> bool:
        """
        登录聚宽
        返回：是否登录成功
        """
        try:
            from jqdatasdk import auth
            auth(JQ_USERNAME, JQ_PASSWORD)
            logger.info("✅ 聚宽登录成功")
            return True
        except Exception as e:
            logger.error(f"❌ 聚宽登录失败: {e}")
            return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股股票列表 - 聚宽API
        返回：包含所有A股实时行情的DataFrame
        """
        try:
            from jqdatasdk import get_all_securities
            
            # 获取所有股票信息
            securities = get_all_securities(types=['stock'])
            
            # 转换为DataFrame
            stock_df = pd.DataFrame(securities).T
            
            # 获取实时行情
            from jqdatasdk import get_price
            stocks = list(stock_df.index)
            
            # 获取最新价格
            price_df = get_price(
                stocks,
                start_date=datetime.now().strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                frequency='daily',
                fields=['open', 'close', 'high', 'low', 'volume', 'turnover_rate', 'pe', 'pb']
            )
            
            # 扁平化MultiIndex
            if isinstance(price_df.columns, pd.MultiIndex):
                price_df = price_df.droplevel(1, axis=1)
            
            logger.info(f"✅ 获取到 {len(price_df)} 只股票")
            return price_df
            
        except Exception as e:
            logger.error(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_code: str) -> Dict:
        """
        获取财务数据 - 聚宽API
        参数：stock_code - 股票代码
        返回：包含财务指标的字典
        """
        try:
            from jqdatasdk import get_fundamentals
            
            # 转换为聚宽代码格式
            jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
            
            # 获取财务数据
            financial_df = get_fundamentals(
                pd.Index([jq_code]),
                date=None,  # 最新财报
                fields=[
                    'roe', 'net_profit_margin', 'gross_profit_margin',
                    'debt_to_assets', 'current_ratio',
                    'revenue_growth', 'net_profit_growth'
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
            return {}
    
    def get_price_history(self, stock_code: str, days: int = 180) -> pd.DataFrame:
        """
        获取历史价格数据 - 聚宽API
        参数：
            stock_code - 股票代码
            days - 获取多少天的数据
        返回：包含历史价格的DataFrame
        """
        try:
            from jqdatasdk import get_price
            
            # 转换代码格式
            jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
            
            # 计算开始日期
            start_date = (datetime.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
            
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
            
        except Exception as e:
            return pd.DataFrame()
    
    def calculate_value_factors(self, stock: Dict) -> Dict:
        """
        计算价值因子
        """
        return {
            "PE_TTM": stock.get("pe", 0),
            "PB": stock.get("pb", 0),
            "PS_TTM": 0,
            "dividend_yield": 0,
        }
    
    def calculate_growth_factors(self, financial: Dict) -> Dict:
        """
        计算成长因子
        """
        return {
            "revenue_growth": financial.get("revenue_growth", 0),
            "profit_growth": financial.get("profit_growth", 0),
            "ROE": financial.get("ROE", 0),
            "ROA": financial.get("ROA", 0),
            "gross_margin": financial.get("gross_margin", 0),
        }
    
    def calculate_momentum_factors(self, price_df: pd.DataFrame) -> Dict:
        """
        计算动量因子
        """
        if price_df.empty:
            return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}
        
        try:
            n = len(price_df)
            
            # 1个月
            if n >= 20:
                momentum_1m = (price_df['close'].iloc[-1] / price_df['close'].iloc[-20] - 1) * 100
            else:
                momentum_1m = 0
            
            # 3个月
            if n >= 60:
                momentum_3m = (price_df['close'].iloc[-1] / price_df['close'].iloc[-60] - 1) * 100
            else:
                momentum_3m = momentum_1m
            
            # 6个月
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
    
    def calculate_quality_factors(self, financial: Dict) -> Dict:
        """
        计算质量因子
        """
        return {
            "debt_ratio": financial.get("debt_ratio", 0),
            "current_ratio": financial.get("current_ratio", 0),
            "net_profit_margin": financial.get("net_profit_margin", 0),
            "ocf_to_profit": 0,
        }
    
    def calculate_technical_factors(self, stock: Dict, price_df: pd.DataFrame) -> Dict:
        """
        计算技术因子
        """
        turnover = stock.get("turnover_rate", 0) or 0
        
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
    
    def normalize_factor(self, value: float, direction: int) -> float:
        """
        标准化因子（0-100分）
        """
        if value is None or value == 0 or value == float('inf') or value == float('-inf'):
            return 50
        
        if direction == -1:
            if value <= 0:
                return 80
            elif value > 100:
                return 20
            else:
                return max(0, min(100, 100 - value))
        else:
            return max(0, min(100, value))
    
    def calculate_factor_score(self, factors: Dict, category: str) -> float:
        """
        计算类别因子得分
        """
        category_factors = {
            "value": ["PE_TTM", "PB", "PS_TTM", "dividend_yield"],
            "growth": ["revenue_growth", "profit_growth", "ROE", "ROA", "gross_margin"],
            "momentum": ["momentum_1m", "momentum_3m", "momentum_6m"],
            "quality": ["debt_ratio", "current_ratio", "net_profit_margin", "ocf_to_profit"],
            "technical": ["RSI", "turnover_rate", "volatility"],
        }
        
        total_score = 0
        total_weight = 0
        
        for factor in category_factors.get(category, []):
            if factor in factors:
                value = factors[factor]
                direction = self.factor_direction.get(factor, 1)
                weight = self.factor_weights.get(factor, 0.1)
                
                score = self.normalize_factor(value, direction)
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 50
    
    def filter_stocks(self, stocks: pd.DataFrame) -> pd.DataFrame:
        """
        过滤股票
        """
        filtered = stocks.copy()
        
        # 过滤PE/PB为负
        filtered = filtered[filtered['pe'] > 0]
        filtered = filtered[filtered['pb'] > 0]
        
        # 过滤停牌
        filtered = filtered[filtered['close'] > 0]
        
        logger.info(f"📊 过滤后剩余 {len(filtered)} 只股票")
        return filtered
    
    def select_stocks(self, stocks: pd.DataFrame) -> List[Dict]:
        """
        核心选股函数
        """
        logger.info("🔍 开始多因子选股...")
        
        stocks = self.filter_stocks(stocks)
        
        if len(stocks) < self.config["stock_count"]:
            logger.warning(f"⚠️ 股票数量不足 {self.config['stock_count']} 只")
        
        results = []
        
        for idx, row in stocks.iterrows():
            # 聚宽返回的索引格式：'600519.XSHG'
            if isinstance(idx, str):
                stock_code = idx.split('.')[0]
            else:
                stock_code = str(idx)
            
            stock_info = {
                "code": stock_code,
                "name": stock_code,
                "price": row.get('close', 0),
                "change_pct": row.get('pct_change', 0) * 100 if 'pct_change' in row else 0,
                "pe": row.get('pe', 0),
                "pb": row.get('pb', 0),
                "turnover_rate": row.get('turnover_rate', 0) or 0,
            }
            
            # 获取财务数据
            try:
                financial = self.get_financial_data(stock_code)
            except:
                financial = {}
            
            # 获取历史价格
            try:
                price_df = self.get_price_history(stock_code)
            except:
                price_df = pd.DataFrame()
            
            # 计算所有因子
            factors = {}
            factors.update(self.calculate_value_factors(stock_info))
            factors.update(self.calculate_growth_factors(financial))
            factors.update(self.calculate_momentum_factors(price_df))
            factors.update(self.calculate_quality_factors(financial))
            factors.update(self.calculate_technical_factors(stock_info, price_df))
            
            # 计算类别得分
            category_scores = {
                "value": self.calculate_factor_score(factors, "value"),
                "growth": self.calculate_factor_score(factors, "growth"),
                "momentum": self.calculate_factor_score(factors, "momentum"),
                "quality": self.calculate_factor_score(factors, "quality"),
                "technical": self.calculate_factor_score(factors, "technical"),
            }
            
            # 计算综合得分
            final_score = sum(
                category_scores[cat] * self.config["weights"][cat] 
                for cat in category_scores
            )
            
            results.append({
                **stock_info,
                "factors": factors,
                "category_scores": category_scores,
                "final_score": final_score,
            })
        
        # 排序并选前N只
        results.sort(key=lambda x: x["final_score"], reverse=True)
        selected = results[:self.config["stock_count"]]
        
        logger.info(f"✅ 选出 {len(selected)} 只股票")
        
        return selected
    
    def format_report(self, selected_stocks: List[Dict]) -> str:
        """
        生成报告
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = f"📊 多因子选股报告 - {today}\n"
        report += "=" * 50 + "\n\n"
        
        report += f"【策略参数】\n"
        report += f"选股数量：{self.config['stock_count']}只\n"
        report += f"换仓频率：{'月度' if self.config['rebalance_freq'] == 'M' else '季度'}\n"
        report += f"因子权重：价值{self.config['weights']['value']*100:.0f}% | "
        report += f"成长{self.config['weights']['growth']*100:.0f}% | "
        report += f"动量{self.config['weights']['momentum']*100:.0f}% | "
        report += f"质量{self.config['weights']['quality']*100:.0f}% | "
        report += f"技术{self.config['weights']['technical']*100:.0f}%\n\n"
        
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
    
    def send_to_telegram(self, report: str) -> bool:
        """
        发送报告到Telegram
        """
        logger.info("📤 发送到Telegram...")
        
        cmd = [
            "openclaw",
            "message",
            "send",
            "--channel", "telegram",
            "--target", "8303320872",
            "--message", report
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ 报告已发送到Telegram")
                return True
            else:
                logger.error(f"❌ 发送失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 发送异常: {e}")
            return False
    
    def run(self):
        """
        主运行函数
        """
        logger.info("🚀 开始多因子选股...")
        
        # 登录聚宽
        if not self.login():
            logger.error("❌ 聚宽登录失败，无法获取数据")
            return None
        
        # 获取股票列表
        stocks = self.get_stock_list()
        
        if stocks.empty:
            logger.error("❌ 无法获取股票数据")
            return None
        
        # 选股
        selected = self.select_stocks(stocks)
        
        # 生成报告
        report = self.format_report(selected)
        
        # 发送到Telegram
        self.send_to_telegram(report)
        
        logger.info("✨ 选股完成")
        
        return report


def main():
    selector = MultiFactorStockSelector()
    report = selector.run()
    
    if report:
        print("\n" + "=" * 50)
        print(report)
        print("=" * 50)


if __name__ == "__main__":
    main()
