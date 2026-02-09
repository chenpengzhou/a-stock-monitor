#!/usr/bin/env python3
"""
LowVol 策略配置
"""

class LowVolConfig:
    """低波策略配置"""
    
    # 默认配置
    DEFAULT = {
        # 因子权重
        'volatility_weight': 0.40,
        'atr_weight': 0.25,
        'beta_weight': 0.20,
        'quality_weight': 0.15,
        
        # 选股条件
        'volatility_percentile': 30,  # 波动率最低30%
        'atr_threshold': 0.5,  # ATR < 5日均值
        'beta_threshold': 0.8,  # Beta < 0.8
        'min_roe': 10.0,  # ROE > 10%
        
        # 仓位管理
        'bear_position': 0.40,  # 熊市40%
        'neutral_position': 0.20,  # 震荡市20%
        'bull_position': 0.00,  # 牛市0%
        
        # 风控
        'stop_loss': 0.10,
        'take_profit': 0.30,
        
        # 选股数量
        'top_n': 30,
    }
    
    def __init__(self, custom: Dict = None):
        """
        初始化配置
        
        Args:
            custom: 自定义配置
        """
        self.config = self.DEFAULT.copy()
        if custom:
            self.config.update(custom)
    
    def get(self, key: str, default=None):
        """获取配置"""
        return self.config.get(key, default)
    
    def get_position(self, market_type: str) -> float:
        """
        根据市场类型获取仓位
        
        Args:
            market_type: bull/bear/neutral
        
        Returns:
            仓位比例
        """
        positions = {
            'bear': self.config['bear_position'],
            'neutral': self.config['neutral_position'],
            'bull': self.config['bull_position'],
        }
        return positions.get(market_type, 0.2)


if __name__ == "__main__":
    print("LowVol Config Module loaded")
    config = LowVolConfig()
    print(f"Default config: {config.DEFAULT}")
