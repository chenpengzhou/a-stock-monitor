# 低波动率策略 (Low Volatility Strategy)

## 概述

本项目实现了一个低波动率选股策略，基于"低波动异象"（Low Volatility Anomaly）理论，即低波动股票长期表现优于高波动股票。

**核心假设**：低波动股票风险调整后收益更高，长期累计收益优于高波动股票。

## 预期表现（产品设计文档）

| 指标 | 保守估计 | 中性估计 | 乐观估计 |
|------|----------|----------|----------|
| **年化收益率** | 8% | 10% | 12% |
| **年化波动率** | 12% | 15% | 18% |
| **最大回撤** | -6% | -8% | -10% |
| **夏普比率** | 0.67 | 0.67 | 0.67 |

## 目录结构

```
lowvol_strategy/
├── __init__.py              # 主入口
├── config/
│   ├── __init__.py
│   └── lowvol_config.py     # 策略配置
├── factors/
│   ├── __init__.py
│   ├── volatility_factor.py # 波动率因子
│   ├── atr_factor.py        # ATR因子
│   ├── beta_factor.py       # Beta因子
│   ├── quality_factor.py    # 质量因子
│   └── composite_score.py   # 复合评分
├── selection/
│   ├── __init__.py
│   └── stock_selector.py    # 选股器
├── position/
│   ├── __init__.py
│   └── position_manager.py  # 仓位管理
├── backtest/
│   ├── __init__.py
│   ├── backtest_engine.py   # 回测引擎
│   └── performance.py       # 绩效分析
├── tests/
│   ├── __init__.py
│   └── self_test.py         # 自测验证
└── README.md                # 本文档
```

## 快速开始

### 安装依赖

```bash
pip install pandas numpy
```

### 基本使用

```python
from lowvol_strategy import LowVolStrategy, LowVolConfig

# 使用默认配置
strategy = LowVolStrategy()

# 加载数据（需要包含必要字段）
# data = pd.DataFrame({
#     'code': 股票代码,
#     'date': 交易日期,
#     'close': 收盘价,
#     'high': 最高价,
#     'low': 最低价,
#     'volatility': 年化波动率,
#     'beta': Beta系数,
#     'atr_percent': ATR百分比,
#     'roe': ROE,
#     'debt_ratio': 资产负债率,
#     'dividend_yield': 股息率,
#     'quality_score': 质量得分,
#     'industry': 行业,
#     'listing_days': 上市天数,
#     'avg_turnover': 日均成交额
# })
# strategy.load_data(data)

# 运行回测
# results = strategy.run_backtest(start_date='2020-01-01', end_date='2024-12-31')

# 打印结果
# strategy.print_results()
```

### 运行自测

```python
from lowvol_strategy.tests import SelfTest

# 运行所有测试
tester = SelfTest()
results = tester.run_all_tests()

# 打印结果
tester.print_results()
```

或直接运行：

```bash
python -m lowvol_strategy.tests.self_test
```

## 策略详解

### 因子计算

1. **波动率因子**（权重: 35%）
   - 计算方法：`σ = StdDev(日收益率, N日) × √250`
   - 默认周期：20日
   - 作用：衡量股票波动水平

2. **ATR因子**（权重: 25%）
   - 计算方法：`ATR = Mean(TrueRange, 14)`, `ATR% = ATR / 收盘价 × 100%`
   - 默认周期：14日
   - 作用：衡量真实波动幅度

3. **Beta因子**（权重: 20%）
   - 计算方法：`β = Cov(股票收益, 市场收益) / Var(市场收益)`
   - 默认周期：60日
   - 作用：控制系统性风险暴露

4. **质量因子**（权重: 20%）
   - ROE > 5%
   - 资产负债率 < 70%
   - 股息率 > 0.5%
   - 作用：排除基本面恶化的低波股票

### 选股流程

```
1. 基础筛选：上市满180日，日均成交额>3000万
2. 财务筛选：ROE>5%，资产负债率<70%，股息率>0.5%
3. 低波筛选：年化波动率<30%，Beta<1.2
4. 低波评分：计算4因子加权综合得分
5. 排序选股：按综合得分升序排列（低波优先）
6. 持仓构建：选取Top 30只，等权配置
```

### 风控参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 单只权重上限 | 5% | 避免过度集中 |
| 行业权重上限 | 20% | 行业分散 |
| Beta上限 | 1.2 | 控制系统性风险 |
| 波动率上限 | 30% | 排除高波动股票 |

## 配置文件

所有参数可在 `config/lowvol_config.py` 中修改：

```python
class LowVolConfig:
    # 因子参数
    VOLATILITY_WINDOW = 20      # 波动率计算周期
    ATR_WINDOW = 14              # ATR计算周期
    BETA_WINDOW = 60             # Beta计算周期
    
    # 选股参数
    TOP_N_HOLDINGS = 30         # 持仓数量
    MIN_LISTING_DAYS = 180      # 最低上市天数
    MIN_AVG_TURNOVER = 3000     # 最低日均成交额
    
    # 风控参数
    MAX_SINGLE_WEIGHT = 0.05    # 单只权重上限
    MAX_INDUSTRY_WEIGHT = 0.20  # 行业权重上限
    
    # 回测参数
    INITIAL_CAPITAL = 1000000   # 初始资金
    TRANSACTION_COST = 0.001    # 交易成本
```

## 扩展使用

### 自定义因子权重

```python
from lowvol_strategy import LowVolConfig, CompositeLowVolScore

config = LowVolConfig()
config.VOLATILITY_WEIGHT = 0.40  # 调整波动率权重
config.ATR_WEIGHT = 0.20         # 调整ATR权重
config.BETA_WEIGHT = 0.25        # 调整Beta权重
config.QUALITY_WEIGHT = 0.15     # 调整质量因子权重

strategy = LowVolStrategy(config)
```

### 使用自定义选股器

```python
from lowvol_strategy import LowVolStockSelector, LowVolConfig

config = LowVolConfig()
selector = LowVolStockSelector(config)

# 执行选股
selected, details = selector.select(stock_data, return_details=True)
```

### 单独使用因子计算

```python
from lowvol_strategy.factors import VolatilityFactor, ATRFactor, BetaFactor

# 计算波动率
vol_factor = VolatilityFactor(window=20)
vol = vol_factor.calculate(prices)

# 计算ATR
atr_factor = ATRFactor(window=14)
atr_percent = atr_factor.calculate_atr_percent(high, low, close)

# 计算Beta
beta_factor = BetaFactor(window=60)
beta = beta_factor.calculate_beta(stock_returns, market_returns)
```

## 测试验证

运行自测验证所有模块：

```bash
python -m lowvol_strategy.tests.self_test
```

测试内容包括：
- 波动率因子计算
- ATR因子计算
- Beta因子计算
- 质量因子计算
- 复合评分计算
- 选股器功能
- 仓位管理器
- 回测引擎
- 绩效分析器

## 与动量策略的对比

| 维度 | 低波策略 | 动量策略 |
|------|----------|----------|
| 目标权重 | 40% | 30% |
| 预期年化收益 | 8-12% | 10-15% |
| 预期最大回撤 | -8% | -15% |
| 风险等级 | 中低 | 中高 |
| 核心逻辑 | 低波动优先 | 强势优先 |

低波策略与动量策略组合可以有效分散风险，提高风险调整后收益。

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-02-09 | 初始版本完成 |

## 参考资料

- 产品设计文档: `/home/admin/.openclaw/workspace-product/MOMENTUM_LOWVOL_PRODUCT_DESIGN.md`
- 低波动异象研究: AQR Capital相关研究
- 策略建议报告: `/home/admin/.openclaw/workspace-strategy/STRATEGY_RECOMMENDATION.md`

---

**作者**: AI Agent  
**日期**: 2026-02-09  
**版本**: 1.0
