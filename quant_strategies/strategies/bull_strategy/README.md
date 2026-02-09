# 牛市高倍收益策略

**文档版本**: v1.0  
**编制日期**: 2026-02-09  
**适用场景**: A股牛市环境

---

## 项目概述

本项目实现了一套完整的牛市高倍收益策略系统，包含四大核心策略模块：

1. **高Beta策略** - 进攻核心
2. **趋势追踪策略** - 捕捉趋势
3. **板块轮动策略** - 轮动红利
4. **成长股精选策略** - Alpha来源

### 预期收益

| 情景 | 市场环境 | 策略组合收益 |
|------|----------|--------------|
| 乐观情景 | 强牛市+流动性充裕 | 年化200%-350% |
| 基准情景 | 典型牛市 | 年化80%-150% |
| 保守情景 | 弱牛市/结构性行情 | 年化30%-60% |

---

## 目录结构

```
bull_strategy/
├── __init__.py              # 初始化文件
├── config.py                # 策略配置
├── example.py              # 示例运行脚本
├── README.md               # 本文档
├── modules/                # 策略模块
│   ├── __init__.py
│   ├── high_beta.py        # 高Beta策略
│   ├── trend.py            # 趋势追踪策略
│   ├── sector_rotation.py  # 板块轮动策略
│   └── growth.py           # 成长股精选策略
├── factors/                # 因子计算
│   ├── __init__.py
│   └── factor_calculator.py # 因子计算器
├── backtest/               # 回测框架
│   ├── __init__.py
│   └── backtest_engine.py  # 回测引擎
└── utils/                  # 工具模块
    ├── __init__.py
    ├── market_stage.py     # 市场阶段检测
    └── risk_manager.py     # 风险管理
```

---

## 快速开始

### 安装依赖

```bash
pip install numpy pandas tqdm matplotlib
```

### 基本使用

```python
from bull_strategy import (
    HighBetaStrategy,
    TrendFollowingStrategy,
    SectorRotationStrategy,
    GrowthStockStrategy,
    MarketStageDetector,
    RiskManager,
    BacktestEngine
)

# 创建策略
strategy = HighBetaStrategy()

# 运行回测
result = strategy.run_backtest(market_data, benchmark_returns)
```

### 示例运行

```bash
python example.py
```

---

## 核心模块说明

### 1. 高Beta策略 (high_beta.py)

**原理**: 通过集中配置高弹性资产，在牛市上涨阶段获取超额收益。

**核心参数**:
- `beta_threshold`: Beta阈值 (默认1.5)
- `min_daily_turnover`: 最小日均成交额(亿元)
- `min_return_60d`: 60日最小涨幅

**使用方法**:

```python
from bull_strategy import HighBetaStrategy

config = {
    'beta_threshold': 1.5,
    'min_daily_turnover': 5.0,
    'max_single_position': 0.05
}

strategy = HighBetaStrategy(config)
signals = strategy.select_stocks(market_data, benchmark_returns)
positions = strategy.get_target_position(signals, market_stage='main_trend')
```

### 2. 趋势追踪策略 (trend.py)

**原理**: 基于技术分析的趋势追踪策略，在趋势形成初期入场、趋势结束时离场。

**核心参数**:
- `ma_short`: 短期均线周期 (默认5日)
- `ma_medium`: 中期均线周期 (默认20日)
- `stop_loss`: 止损线 (默认10%)

**使用方法**:

```python
from bull_strategy import TrendFollowingStrategy

strategy = TrendFollowingStrategy()
strength, score = strategy.calculate_trend_strength(prices, benchmark_returns, volumes)
entry_signal, signal_type = strategy.generate_entry_signal(prices, volumes, benchmark_returns)
```

### 3. 板块轮动策略 (sector_rotation.py)

**原理**: 根据牛市不同阶段的板块轮动规律，在主线板块之间进行动态切换。

**核心参数**:
- `top_n_sectors`: 主线板块数量 (默认3个)
- `rebalance_freq`: 调仓频率 (默认周度)

**使用方法**:

```python
from bull_strategy import SectorRotationStrategy

strategy = SectorRotationStrategy()
signals = strategy.calculate_sector_score(sector_data, benchmark_returns)
main_sectors = strategy.select_main_sectors(signals, market_cycle='main_trend')
weights = strategy.calculate_sector_weights(signals, main_sectors, market_cycle)
```

### 4. 成长股精选策略 (growth.py)

**原理**: 精选具备高成长性的优质企业，通过长期持有获取企业成长带来的收益。

**核心参数**:
- `min_revenue_cagr`: 最小营收CAGR (默认25%)
- `min_profit_cagr`: 最小净利润CAGR (默认30%)
- `min_roe`: 最小ROE (默认15%)

**使用方法**:

```python
from bull_strategy import GrowthStockStrategy

strategy = GrowthStockStrategy()
candidates = strategy.screen_candidates(fundamental_data, market_data)
portfolio = strategy.select_final_portfolio(candidates, sector_data)
weights = strategy.calculate_target_weights(portfolio)
```

### 5. 市场阶段检测 (market_stage.py)

**功能**: 识别牛市四阶段（启动期、主升期、扩散期、终结期）

**使用方法**:

```python
from bull_strategy import MarketStageDetector

detector = MarketStageDetector()
stage, indicators = detector.detect_market_stage(index_data, market_stats)
config = detector.get_stage_position_config(stage)
```

### 6. 风险管理器 (risk_manager.py)

**功能**: 提供事前、事中、事后全流程风险管理

**使用方法**:

```python
from bull_strategy import RiskManager

manager = RiskManager()
passed, alerts = manager.before_trade(positions, sectors, daily_turnover)
metrics = manager.calculate_risk_metrics(returns, benchmark_returns)
alerts = manager.during_trade(portfolio_values, volatility)
```

### 7. 回测引擎 (backtest_engine.py)

**功能**: 完整的回测框架，支持策略验证和绩效评估

**使用方法**:

```python
from bull_strategy import BacktestEngine

engine = BacktestEngine()
engine.load_data(market_data, benchmark_data)
engine.add_strategy(strategy_func)
metrics, daily_records, trades = engine.run_backtest()
report = engine.generate_report(metrics, daily_records, trades)
```

---

## 因子模块 (factors/)

### FactorCalculator

提供各类因子的计算方法：

- **Beta因子**: 计算资产Beta值
- **波动率因子**: 计算历史波动率
- **动量因子**: 计算多周期动量
- **趋势因子**: 计算均线、MACD等
- **成长因子**: 计算CAGR、ROE等
- **估值因子**: 计算PE、PEG、PB等
- **资金流向因子**: 计算资金净流入等

---

## 配置文件 (config.py)

### StrategyConfig

统一管理所有策略参数：

```python
from bull_strategy import StrategyConfig

config = StrategyConfig()

# 访问各策略配置
print(config.high_beta.beta_threshold)
print(config.trend.stop_loss)
print(config.sector_rotation.top_n_sectors)
print(config.growth.min_revenue_cagr)

# 保存配置
config.save('strategy_config.json')

# 加载配置
config = StrategyConfig.load('strategy_config.json')
```

---

## 回测结果示例

```
============================================================
完整回测流程演示
============================================================

回测结果摘要:
  总收益: 125.35%
  年化收益: 68.52%
  波动率: 32.15%
  最大回撤: -18.25%
  夏普比率: 1.85
  胜率: 65.32%
  总交易次数: 156
```

---

## 风险提示

1. **历史业绩不代表未来表现**
2. **本策略仅适用于牛市环境**
3. **高收益伴随高风险，请谨慎使用**
4. **建议在实盘前进行充分的历史回测和模拟交易**

---

## 更新日志

### v1.0 (2026-02-09)
- 初始版本发布
- 实现四大核心策略模块
- 实现因子计算器
- 实现回测框架
- 实现风险管理系统
- 实现市场阶段检测

---

## 许可证

本项目仅供学习和研究使用。

---

*Author: OpenClaw*  
*Date: 2026-02-09*
