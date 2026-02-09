#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量策略调参脚本
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/commodity-monitor/src')

import pandas as pd
import numpy as np
import json
import random
import time
from datetime import datetime
from pathlib import Path
from momentum_backtest import MomentumBacktest


def generate_params():
    """生成参数组合"""
    
    # 因子权重组合
    mom3_ws = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]  # 8档
    mom6_ws = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]          # 7档
    mom12_ws = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]              # 6档
    rsi_ws = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]                 # 6档
    vol_ws = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]                 # 6档
    
    for m3 in mom3_ws:
        for m6 in mom6_ws:
            for m12 in mom12_ws:
                for rsi in rsi_ws:
                    for vol in vol_ws:
                        total = m3 + m6 + m12 + rsi + vol
                        # 归一化权重
                        yield {
                            'weights': {
                                'mom_3m': m3 / total,
                                'mom_6m': m6 / total,
                                'mom_12m': m12 / total,
                                'rsi': rsi / total,
                                'volume_mom': vol / total,
                            }
                        }
    
    # 止损参数
    for stop_loss in [0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30]:
        yield {'stop_loss': stop_loss}
    
    # 仓位参数
    for position in [0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]:
        yield {'position': position}


def run_backtest(weights, stop_loss, position, stock_data_dict):
    """运行回测"""
    
    backtest = MomentumBacktest({
        'initial_capital': 100000,
        'rebalance_months': 3,
        'stop_loss': stop_loss,
        'position_size': position,
        'market_type': 'all',
    })
    
    results = backtest.run_backtest(
        stock_data_dict=stock_data_dict,
        start_date=datetime(2006, 1, 1),  # 牛市年份开始
        end_date=datetime(2020, 12, 31)
    )
    
    return results


def normalize_weights(w_list):
    """归一化权重"""
    total = sum(w_list)
    return [w / total for w in w_list]


def main():
    """主函数"""
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(f"/home/admin/.openclaw/workspace/commodity-monitor/reports/momentum/{run_id}")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("动量策略调参 - 全量版")
    print("=" * 70)
    
    # 参数空间
    mom3_ws = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]  # 8档
    mom6_ws = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]          # 7档
    mom12_ws = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]              # 6档
    rsi_ws = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]                 # 6档
    vol_ws = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]                 # 6档
    stops = [0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30]      # 8档
    positions = [0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]  # 8档
    
    # 计算总组合数
    weight_combos = len(mom3_ws) * len(mom6_ws) * len(mom12_ws) * len(rsi_ws) * len(vol_ws)
    total = weight_combos * len(stops) * len(positions)
    
    print(f"因子权重组合: {weight_combos:,}")
    print(f"总组合数: {total:,}")
    print()
    
    # 准备股票数据
    print("准备股票数据...")
    stock_data_dict = prepare_mock_data()
    
    best_return = float('-inf')
    best_params = None
    combinations = 0
    
    start_time = datetime.now()
    
    for m3 in mom3_ws:
        for m6 in mom6_ws:
            for m12 in mom12_ws:
                for rsi in rsi_ws:
                    for vol in vol_ws:
                        weights = normalize_weights([m3, m6, m12, rsi, vol])
                        
                        for stop in stops:
                            for pos in positions:
                                combinations += 1
                                
                                try:
                                    results = run_backtest(
                                        weights, stop, pos, stock_data_dict
                                    )
                                    ret = results['total_return']
                                    
                                    if ret > best_return:
                                        best_return = ret
                                        best_params = {
                                            'weights': {
                                                'mom_3m': round(weights[0], 3),
                                                'mom_6m': round(weights[1], 3),
                                                'mom_12m': round(weights[2], 3),
                                                'rsi': round(weights[3], 3),
                                                'volume_mom': round(weights[4], 3),
                                            },
                                            'stop_loss': stop,
                                            'position': pos,
                                        }
                                        elapsed = (datetime.now() - start_time).total_seconds()
                                        print(f"[{combinations:,}/{total:,}] 🔥 新最优: {ret:.2f}% (用时: {elapsed:.0f}秒)")
                                    
                                    elif combinations % 10000 == 0:
                                        elapsed = (datetime.now() - start_time).total_seconds()
                                        eta = (elapsed / combinations) * (total - combinations) / 60
                                        print(f"[{combinations:,}/{total:,}] 最优: {best_return:.2f}% 预计剩余: {eta:.0f}分钟")
                                        
                                except Exception as e:
                                    continue
    
    # 保存结果
    result = {
        'run_id': run_id,
        'total_combinations': combinations,
        'best_return': best_return,
        'best_params': best_params,
    }
    
    with open(report_dir / 'FINAL.json', 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("=" * 70)
    print(f"✅ 完成! 最优收益: {best_return:.2f}%")
    print(f"用时: {total_time/60:.1f}分钟")
    print(f"参数: {best_params}")
    print("=" * 70)


def prepare_mock_data():
    """准备模拟股票数据"""
    
    np.random.seed(42)
    dates = pd.date_range(start='2005-01-01', end='2024-12-31', freq='D')
    
    stock_data = {}
    for i in range(50):
        code = f'600{100+i}'
        
        # 创建不同趋势的股票
        if i < 10:  # 强势股
            trend = np.random.randn() * 0.0008 + 0.0004
        elif i < 30:  # 普通股票
            trend = np.random.randn() * 0.0005 + 0.0001
        else:  # 弱势股
            trend = np.random.randn() * 0.0005 - 0.0002
        
        close = np.cumsum(np.random.randn(len(dates)) * 2 + trend) + 100
        
        stock_data[code] = pd.DataFrame({
            'close': close,
            'volume': np.abs(np.random.randn(len(dates)) * 1000000 + 5000000)
        }, index=dates)
    
    return stock_data


if __name__ == '__main__':
    main()
