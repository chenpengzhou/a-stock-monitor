#!/usr/bin/env python3
"""
低波动率策略 - 自测验证脚本
============================

用于验证策略各模块的功能是否正常。

使用方法（推荐）:
    cd /home/admin/.openclaw/workspace-dev/lowvol_strategy
    python3 -m self_test

作者: AI Agent
日期: 2026-02-09
版本: 1.1
"""

import sys
import os

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 现在使用模块导入
from lowvol_strategy.tests import SelfTest


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("低波动率策略 - 自测验证")
    print("=" * 60 + "\n")
    
    tester = SelfTest()
    tester.run_all_tests()
    tester.print_results()
    
    # 返回退出码
    passed = sum(1 for r in tester.test_results if r['passed'])
    total = len(tester.test_results)
    
    if passed == total:
        print(f"\n✓ 所有 {total} 个测试通过！\n")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试未通过\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
