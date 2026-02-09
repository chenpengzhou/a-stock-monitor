"""
低波动率策略 - 仓位管理模块
============================

本模块提供仓位管理功能，包括：
1. 等权配置
2. 行业权重控制
3. 动态仓位调整
4. 止损机制

作者: AI Agent
日期: 2026-02-09
版本: 1.0
"""

from .position_manager import PositionManager

__all__ = ['PositionManager']
