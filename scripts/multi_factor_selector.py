#!/usr/bin/env python3
"""
多因子选股系统（测试版）
- 当前使用模拟数据
- 明天接入真实数据源
"""

import sys, os, json, logging, subprocess
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_PATH = Path(__file__).parent
DATA_PATH = PROJECT_PATH / "data"
DATA_PATH.mkdir(parents=True, exist_ok=True)


class MultiFactorStockSelector:
    def __init__(self):
        self.config = {
            "weights": {"value": 0.25, "growth": 0.20, "momentum": 0.15, "quality": 0.25, "technical": 0.15},
            "stock_count": 10,
            "rebalance_freq": "M",
        }
    
    def get_stock_list(self):
        """模拟股票数据（明天接入AkShare真实数据）"""
        import random
        
        stocks = []
        names = ["贵州茅台", "五粮液", "泸州老窖", "山西汾酒", "洋河股份",
                 "海康威视", "大华股份", "中信证券", "华泰证券", "招商银行",
                 "平安银行", "宁波银行", "上海机场", "中国中免", "海螺水泥",
                 "万华化学", "三一重工", "保利地产", "万科A", "格力电器"]
        
        for i, name in enumerate(names):
            change = random.uniform(-3, 5)
            stocks.append({
                "code": f"{600000+i}",
                "name": name,
                "price": round(random.uniform(20, 200), 2),
                "change_pct": round(change, 2),
                "pe": round(random.uniform(10, 50), 1),
                "pb": round(random.uniform(1, 10), 2),
            })
        
        logger.info(f"📊 获取 {len(stocks)} 只股票（模拟数据）")
        return stocks
    
    def select_stocks(self, stocks):
        """选股"""
        import random
        
        results = []
        for stock in stocks:
            cats = {
                "value": random.uniform(40, 80),
                "growth": random.uniform(40, 80),
                "momentum": random.uniform(40, 80),
                "quality": random.uniform(40, 80),
                "technical": random.uniform(40, 80),
            }
            
            final = sum(cats[k] * self.config["weights"][k] for k in cats)
            
            results.append({
                **stock,
                "category_scores": cats,
                "final_score": round(final, 1),
            })
        
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:self.config["stock_count"]]
    
    def format_report(self, stocks):
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = f"📊 多因子选股报告 - {today}\n"
        report += "=" * 50 + "\n\n"
        
        report += f"【策略参数】\n"
        report += f"选股数量：{self.config['stock_count']}只\n"
        report += f"换仓频率：{'月度' if self.config['rebalance_freq'] == 'M' else '季度'}\n"
        report += f"因子权重：价值25% | 成长20% | 动量15% | 质量25% | 技术15%\n\n"
        
        report += "【选股结果】\n"
        report += "-" * 50 + "\n"
        
        for i, s in enumerate(stocks, 1):
            emoji = "📈" if s["change_pct"] > 0 else "📉"
            report += f"{i:2d}. {s['code']} {s['name']}\n"
            report += f"    价格：¥{s['price']:.2f} {emoji} {s['change_pct']:+.2f}%\n"
            report += f"    综合得分：{s['final_score']}/100\n"
            report += f"    价值:{s['category_scores']['value']:.0f} 成长:{s['category_scores']['growth']:.0f} "
            report += f"动量:{s['category_scores']['momentum']:.0f} 质量:{s['category_scores']['quality']:.0f}\n"
            report += "-" * 50 + "\n"
        
        report += "\n💡 数据源：模拟数据（AkShare网络不稳定，明天重试）\n"
        report += "⚠️ 本报告仅供分析，不构成投资建议\n"
        
        return report
    
    def send_to_telegram(self, report):
        cmd = ["openclaw", "message", "send", "--channel", "telegram", "--target", "8303320872", "--message", report]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ 已发送到Telegram")
                return True
            else:
                logger.error(f"❌ 发送失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 异常: {e}")
            return False
    
    def run(self):
        logger.info("🚀 开始选股...")
        
        stocks = self.get_stock_list()
        selected = self.select_stocks(stocks)
        report = self.format_report(selected)
        
        self.send_to_telegram(report)
        
        today = datetime.now().strftime("%Y-%m-%d")
        with open(f"/home/admin/.openclaw/workspace/commodity-monitor/data/stock_report_{today}.txt", "w") as f:
            f.write(report)
        
        logger.info("✨ 完成")
        return report


if __name__ == "__main__":
    selector = MultiFactorStockSelector()
    report = selector.run()
    print("\n" + "=" * 50)
    print(report)
    print("=" * 50)
