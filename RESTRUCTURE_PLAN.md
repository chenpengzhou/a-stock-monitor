# 项目重构方案

## 目标
重新整理项目结构，符合人类阅读习惯

## 新结构
```
quant_strategies/
├── docs/
│   └── README.md
├── strategies/
│   ├── bull_strategy/
│   ├── lowvol_strategy/
│   └── momentum_strategy/
├── scripts/
├── data/
└── tests/
```

## 执行步骤
1. 创建新目录结构
2. 移动代码文件
3. 更新 import 语句
4. 测试运行
```
