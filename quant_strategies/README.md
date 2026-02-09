# Quant Strategies

量化投资策略项目

## 项目结构

```
quant_strategies/
├── docs/              # 文档
├── strategies/        # 策略模块
│   ├── bull_strategy/     # 牛策略
│   ├── lowvol_strategy/    # 低波策略
│   └── momentum_strategy/  # 动量策略
├── scripts/          # 脚本
├── data/             # 数据
└── tests/            # 测试
```

## 策略说明

### Bull Strategy
高收益高风险策略，适用于牛市环境

### LowVol Strategy
低波动策略，适用于熊市环境

### Momentum Strategy
动量策略，适用于震荡市环境

## 使用方法

```bash
# 运行回测
python scripts/run_backtest.py --strategy bull

# 运行测试
pytest tests/
```

---
*最后更新: 2026-02-09*
