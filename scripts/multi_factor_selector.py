#!/usr/bin/env python3
"""
多因子选股系统
- 数据源：AkShare（免费开源A股数据）
- 因子：21个因子（价值、成长、动量、质量、技术）
- 选股：每月选10只
- 推送：Telegram
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

# 配置日志
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


class MultiFactorStockSelector:
    """多因子选股器"""
    
    def __init__(self):
        self.config = {
            # 因子权重（可调）
            "weights": {
                "value": 0.25,
                "growth": 0.20,
                "momentum": 0.15,
                "quality": 0.25,
                "technical": 0.15,
            },
            # 选股参数
            "stock_count": 10,
            "rebalance_freq": "M",  # M=月度, Q=季度
            # 风控参数
            "max_position": 0.15,
            "min_market_cap": 100,  # 亿
            # 过滤条件
            "excluded_industries": ["银行", "房地产", "保险"],
            "st_filter": True,
            "new_stock_filter": True,  # 上市不满6个月
        }
        
        self.factor_direction = {
            # 价值因子（越低越好 -> 反向）
            "PE_TTM": -1,       # 市盈率越低越好
            "PB": -1,           # 市净率越低越好
            "PS_TTM": -1,       # 市销率越低越好
            "dividend_yield": 1,  # 股息率越高越好
            # 成长因子（越高越好）
            "revenue_growth": 1,   # 营收增速
            "profit_growth": 1,    # 利润增速
            "ROE": 1,              # 净资产收益率
            "ROA": 1,             # 资产收益率
            "gross_margin": 1,    # 毛利率
            # 动量因子（越高越好）
            "momentum_1m": 1,     # 近1月涨幅
            "momentum_3m": 1,     # 近3月涨幅
            "momentum_6m": 1,     # 近6月涨幅
            # 质量因子
            "debt_ratio": -1,     # 资产负债率越低越好
            "current_ratio": 1,   # 流动比率越高越好
            "net_profit_margin": 1, # 净利润率越高越好
            "ocf_to_profit": 1,   # 经营现金流/净利润越高越好
            # 技术因子
            "RSI": -1,            # RSI偏低好（超卖）
            "turnover_rate": 1,   # 换手率适中
            "volatility": -1,     # 波动率越低越好
        }
        
        # 因子与权重（可调）
        self.factor_weights = {
            # 价值因子权重
            "PE_TTM": 0.30,
            "PB": 0.30,
            "PS_TTM": 0.20,
            "dividend_yield": 0.20,
            # 成长因子权重
            "revenue_growth": 0.25,
            "profit_growth": 0.25,
            "ROE": 0.20,
            "ROA": 0.15,
            "gross_margin": 0.15,
            # 动量因子权重
            "momentum_1m": 0.30,
            "momentum_3m": 0.40,
            "momentum_6m": 0.30,
            # 质量因子权重
            "debt_ratio": 0.30,
            "current_ratio": 0.25,
            "net_profit_margin": 0.25,
            "ocf_to_profit": 0.20,
            # 技术因子权重
            "RSI": 0.40,
            "turnover_rate": 0.30,
            "volatility": 0.30,
        }
        
        self.stock_data = {}
    
    def import_akshare(self):
        """导入AkShare"""
        try:
            import akshare as ak
            return ak
        except ImportError:
            logger.error("AkShare未安装，请运行: pip install akshare")
            return None
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股实时行情"""
        import akshare as ak
        
        logger.info("📥 获取A股行情数据...")
        
        try:
            # 获取实时行情
            stock_df = ak.stock_zh_a_spot_em()
            
            logger.info(f"✅ 获取到 {len(stock_df)} 只股票")
            return stock_df
            
        except Exception as e:
            logger.error(f"❌ 获取行情失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_code: str) -> Dict:
        """获取财务数据"""
        import akshare as ak
        
        try:
            # 获取财务指标
            financial_df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            if financial_df.empty:
                return {}
            
            latest = financial_df.iloc[0]
            
            return {
                "ROE": float(latest.get("净资产收益率(%)", 0) or 0),
                "ROA": float(latest.get("资产报酬率(%)", 0) or 0),
                "gross_margin": float(latest.get("毛利率(%)", 0) or 0),
                "net_profit_margin": float(latest.get("净利率(%)", 0) or 0),
                "debt_ratio": float(latest.get("资产负债率(%)", 0) or 0),
                "revenue_growth": float(latest.get("营业收入增长率(%)", 0) or 0),
                "profit_growth": float(latest.get("净利润增长率(%)", 0) or 0),
            }
            
        except Exception as e:
            return {}
    
    def get_price_history(self, stock_code: str, days: int = 180) -> pd.DataFrame:
        """获取历史价格数据"""
        import akshare as ak
        
        try:
            # 转换为聚宽格式代码
            jq_code = f"{stock_code}.XSHG" if stock_code.startswith("6") else f"{stock_code}.SZSE"
            
            # 获取日线数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date="20250101")
            
            if df.empty:
                return pd.DataFrame()
            
            # 计算动量
            df = df.sort_values('日期')
            
            # 计算涨跌幅
            df['pct_change'] = df['收盘'].pct_change()
            
            return df
            
        except Exception as e:
            return pd.DataFrame()
    
    def calculate_value_factors(self, stock: Dict) -> Dict:
        """计算价值因子"""
        return {
            "PE_TTM": stock.get("pe", 0),
            "PB": stock.get("pb", 0),
            "PS_TTM": 0,  # AkShare暂无
            "dividend_yield": stock.get("dividend_yield", 0),
        }
    
    def calculate_growth_factors(self, financial: Dict) -> Dict:
        """计算成长因子"""
        return {
            "revenue_growth": financial.get("revenue_growth", 0),
            "profit_growth": financial.get("profit_growth", 0),
            "ROE": financial.get("ROE", 0),
            "ROA": financial.get("ROA", 0),
            "gross_margin": financial.get("gross_margin", 0),
        }
    
    def calculate_momentum_factors(self, price_df: pd.DataFrame) -> Dict:
        """计算动量因子"""
        if price_df.empty:
            return {"momentum_1m": 0, "momentum_3m": 0, "momentum_6m": 0}
        
        try:
            n = len(price_df)
            
            # 1月涨幅
            if n >= 20:
                momentum_1m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-20] - 1) * 100
            else:
                momentum_1m = 0
            
            # 3月涨幅
            if n >= 60:
                momentum_3m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-60] - 1) * 100
            else:
                momentum_3m = momentum_1m
            
            # 6月涨幅
            if n >= 120:
                momentum_6m = (price_df['收盘'].iloc[-1] / price_df['收盘'].iloc[-120] - 1) * 100
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
        """计算质量因子"""
        return {
            "debt_ratio": financial.get("debt_ratio", 0),
            "current_ratio": financial.get("current_ratio", 0),
            "net_profit_margin": financial.get("net_profit_margin", 0),
            "ocf_to_profit": 0,  # 需要现金流数据
        }
    
    def calculate_technical_factors(self, stock: Dict, price_df: pd.DataFrame) -> Dict:
        """计算技术因子"""
        # 换手率
        turnover = stock.get("turnover_rate", 0) or 0
        
        # RSI
        rsi = 50  # 默认值
        if not price_df.empty:
            try:
                delta = price_df['收盘'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi = float(rsi.iloc[-1]) if not rs.iloc[-1] == 0 else 50
            except:
                rsi = 50
        
        # 波动率
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
        """标准化因子（0-100分）"""
        if value is None or value == 0 or value == float('inf') or value == float('-inf'):
            return 50
        
        # 根据方向转换
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
    
    def calculate_factor_score(self, factors: Dict, category: str) -> float:
        """计算类别因子得分"""
        total_score = 0
        total_weight = 0
        
        category_factors = {
            "value": ["PE_TTM", "PB", "PS_TTM", "dividend_yield"],
            "growth": ["revenue_growth", "profit_growth", "ROE", "ROA", "gross_margin"],
            "momentum": ["momentum_1m", "momentum_3m", "momentum_6m"],
            "quality": ["debt_ratio", "current_ratio", "net_profit_margin", "ocf_to_profit"],
            "technical": ["RSI", "turnover_rate", "volatility"],
        }
        
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
        """过滤股票"""
        filtered = stocks.copy()
        
        # 过滤ST
        if self.config["st_filter"]:
            filtered = filtered[~filtered['名称'].str.contains('ST', na=False)]
        
        # 过滤PE/PB为负
        filtered = filtered[filtered['市盈率-动态'] > 0]
        filtered = filtered[filtered['市净率'] > 0]
        
        # 过滤停牌
        filtered = filtered[filtered['最新价'] > 0]
        
        logger.info(f"📊 过滤后剩余 {len(filtered)} 只股票")
        return filtered
    
    def select_stocks(self, stocks: pd.DataFrame) -> List[Dict]:
        """选股"""
        logger.info("🔍 开始多因子选股...")
        
        # 过滤
        stocks = self.filter_stocks(stocks)
        
        if len(stocks) < self.config["stock_count"]:
            logger.warning(f"⚠️ 股票数量不足 {self.config['stock_count']} 只，使用全部 {len(stocks)} 只")
        
        results = []
        
        for idx, row in stocks.iterrows():
            stock_code = row['代码']
            stock_name = row['名称']
            
            stock_info = {
                "code": stock_code,
                "name": stock_name,
                "price": row['最新价'],
                "change_pct": row['涨跌幅'],
                "pe": row['市盈率-动态'],
                "pb": row['市净率'],
                "turnover_rate": row['换手率'],
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
        
        # 按得分排序
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 选前N只
        selected = results[:self.config["stock_count"]]
        
        logger.info(f"✅ 选出 {len(selected)} 只股票")
        
        return selected
    
    def format_report(self, selected_stocks: List[Dict]) -> str:
        """生成报告"""
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
            name = stock["name"][:8] if len(stock["name"]) > 8 else stock["name"]
            change = stock["change_pct"]
            change_emoji = "📈" if change > 0 else "📉"
            
            report += f"{i:2d}. {stock['code']} {name}\n"
            report += f"    价格：¥{stock['price']:.2f} {change_emoji} {change:+.2f}%\n"
            report += f"    综合得分：{stock['final_score']:.1f}/100\n"
            
            # 分类得分
            cats = stock["category_scores"]
            report += f"    价值:{cats['value']:.0f} 成长:{cats['growth']:.0f} "
            report += f"动量:{cats['momentum']:.0f} 质量:{cats['quality']:.0f} "
            report += f"技术:{cats['technical']:.0f}\n"
            
            # 关键因子
            report += f"    PE:{stock['factors'].get('PE_TTM', 'N/A'):.1f} "
            report += f"ROE:{stock['factors'].get('ROE', 'N/A'):.1f}% "
            report += f"营收增:{stock['factors'].get('revenue_growth', 'N/A'):.1f}%\n"
            report += "-" * 50 + "\n"
        
        report += "\n【因子说明】\n"
        report += "价值(PE/PB)：估值越低越好\n"
        report += "成长(ROE/营收)：业绩增长越高越好\n"
        report += "动量(涨幅)：趋势延续性\n"
        report += "质量(负债率)：财务健康度\n"
        report += "技术(RSI/换手)：短期表现\n"
        
        report += "\n💡 数据来源：AkShare\n"
        report += "⚠️ 本报告仅供分析，不构成投资建议\n"
        
        return report
    
    def save_report(self, report: str):
        """保存报告"""
        today = datetime.now().strftime("%Y-%m-%d")
        report_file = DATA_PATH / f"stock_report_{today}.txt"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"📁 报告已保存: {report_file}")
        return report_file
    
    def send_to_telegram(self, report: str) -> bool:
        """发送到Telegram"""
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
        """主运行函数"""
        logger.info("🚀 开始多因子选股...")
        
        # 获取股票列表
        stocks = self.get_stock_list()
        
        if stocks.empty:
            logger.error("❌ 无法获取股票数据")
            return None
        
        # 选股
        selected = self.select_stocks(stocks)
        
        # 生成报告
        report = self.format_report(selected)
        
        # 保存
        self.save_report(report)
        
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
