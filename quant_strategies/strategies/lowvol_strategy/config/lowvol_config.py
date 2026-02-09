"""
低波动率策略 - 默认配置参数
============================

本模块定义了低波动率策略的所有可配置参数，
包括因子计算参数、选股参数、风控参数等。

核心假设：
- 低波动股票长期表现优于高波动股票
- 低波动股票风险调整后收益更高

参数设计参考产品设计文档 MOMENTUM_LOWVOL_PRODUCT_DESIGN.md

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""


class LowVolConfig:
    """
    低波动率策略配置类
    
    包含所有策略参数，支持通过参数调优优化策略表现。
    """
    
    # ==================== 因子计算参数 ====================
    
    # 波动率因子参数
    VOLATILITY_WINDOW = 20          # 波动率计算周期（交易日）
    VOLATILITY_QUANTILE = 0.30      # 波动率分位数阈值（后30%为低波）
    
    # ATR因子参数
    ATR_WINDOW = 14                 # ATR计算周期（交易日）
    ATR_PERCENTILE = 0.50           # ATR百分比分位数阈值
    
    # Beta因子参数
    BETA_WINDOW = 60                # Beta计算周期（交易日）
    BETA_UPPER_LIMIT = 1.2          # Beta上限阈值
    
    # 市场基准（用于Beta计算）
    BENCHMARK_CODE = 'sh.000001'    # 沪深300指数代码
    
    # ==================== 选股参数 ====================
    
    # 基础筛选参数
    MIN_LISTING_DAYS = 180          # 最低上市天数
    MIN_AVG_TURNOVER = 3000         # 最低日均成交额（万元）
    
    # 财务筛选参数
    MIN_ROE = 5.0                   # 最低ROE（%）
    MAX_DEBT_RATIO = 70.0           # 最高资产负债率（%）
    MIN_DIVIDEND_YIELD = 0.5        # 最低股息率（%）
    
    # 低波筛选参数
    VOLATILITY_UPPER_LIMIT = 30.0   # 年化波动率上限（%）
    
    # 持仓参数
    TOP_N_HOLDINGS = 30             # 持仓数量
    REBALANCE_FREQUENCY = 'monthly' # 调仓频率
    
    # ==================== 因子权重参数 ====================
    
    # 复合低波评分因子权重
    VOLATILITY_WEIGHT = 0.35        # 波动率排名权重
    ATR_WEIGHT = 0.25               # ATR百分比排名权重
    BETA_WEIGHT = 0.20              # Beta排名权重
    QUALITY_WEIGHT = 0.20           # 质量因子权重
    
    # ==================== 风控参数 ====================
    
    # 仓位控制
    MAX_SINGLE_WEIGHT = 0.05        # 单只股票最大权重（5%）
    MAX_INDUSTRY_WEIGHT = 0.20      # 行业最大权重（20%）
    
    # 止损参数
    STOP_LOSS_ENABLED = False       # 是否启用止损
    STOP_LOSS_THRESHOLD = -10.0     # 止损阈值（%）
    
    # 动态调整
    ENABLE_INDUSTRY_NEUTRAL = True  # 是否启用行业中性
    
    # ==================== 回测参数 ====================
    
    INITIAL_CAPITAL = 1000000       # 初始资金（元）
    TRANSACTION_COST = 0.001        # 交易成本（0.1%）
    SLIPPAGE = 0.002                # 滑点（0.2%）
    
    # ==================== 辅助参数 ====================
    
    # 评分方向
    # 低波策略：得分越低越好（升序排列）
    HIGHER_IS_BETTER = False
    
    # 输出配置
    ENABLE_LOGGING = True
    LOG_LEVEL = 'INFO'
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        将配置转换为字典
        
        Returns:
            dict: 配置参数字典
        """
        return {
            '因子计算参数': {
                'VOLATILITY_WINDOW': cls.VOLATILITY_WINDOW,
                'VOLATILITY_QUANTILE': cls.VOLATILITY_QUANTILE,
                'ATR_WINDOW': cls.ATR_WINDOW,
                'BETA_WINDOW': cls.BETA_WINDOW,
                'BENCHMARK_CODE': cls.BENCHMARK_CODE,
            },
            '选股参数': {
                'MIN_LISTING_DAYS': cls.MIN_LISTING_DAYS,
                'MIN_AVG_TURNOVER': cls.MIN_AVG_TURNOVER,
                'MIN_ROE': cls.MIN_ROE,
                'MAX_DEBT_RATIO': cls.MAX_DEBT_RATIO,
                'MIN_DIVIDEND_YIELD': cls.MIN_DIVIDEND_YIELD,
                'TOP_N_HOLDINGS': cls.TOP_N_HOLDINGS,
            },
            '因子权重': {
                'VOLATILITY_WEIGHT': cls.VOLATILITY_WEIGHT,
                'ATR_WEIGHT': cls.ATR_WEIGHT,
                'BETA_WEIGHT': cls.BETA_WEIGHT,
                'QUALITY_WEIGHT': cls.QUALITY_WEIGHT,
            },
            '风控参数': {
                'MAX_SINGLE_WEIGHT': cls.MAX_SINGLE_WEIGHT,
                'MAX_INDUSTRY_WEIGHT': cls.MAX_INDUSTRY_WEIGHT,
                'STOP_LOSS_ENABLED': cls.STOP_LOSS_ENABLED,
                'VOLATILITY_UPPER_LIMIT': cls.VOLATILITY_UPPER_LIMIT,
            },
            '回测参数': {
                'INITIAL_CAPITAL': cls.INITIAL_CAPITAL,
                'TRANSACTION_COST': cls.TRANSACTION_COST,
                'SLIPPAGE': cls.SLIPPAGE,
            }
        }
    
    @classmethod
    def print_summary(cls):
        """打印配置摘要"""
        print("\n" + "=" * 60)
        print("低波动率策略配置摘要")
        print("=" * 60)
        
        config_dict = cls.to_dict()
        for section, params in config_dict.items():
            print(f"\n{section}:")
            for key, value in params.items():
                print(f"  {key}: {value}")
        
        print("=" * 60)
