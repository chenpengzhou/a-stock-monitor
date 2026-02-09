# 代码review和技术标准

## 任务目标
审核现有代码，制定技术标准。

## 你的工作

### 1️⃣ 代码review
检查以下脚本的代码质量：
- `scripts/strategies/tune_quality_*.py`
- `scripts/strategies/tune_value.py`
- 其他相关脚本

检查项：
- 代码逻辑是否正确？
- 有没有潜在的 bug？
- 性能问题？
- 安全漏洞？
- 代码规范？

### 2️⃣ 技术标准
制定以下标准文档（`code_review/STANDARDS.md`）：

#### Python 代码规范
- 命名规范（变量、函数、类）
- 注释要求
- 函数长度限制
- 导入规范

#### 回测脚本标准
- 因子计算模块结构
- 参数定义规范
- 回测流程标准
- 结果输出格式

#### 代码review清单
- 检查清单模板
- Review要点
- 提交前检查

### 3️⃣ 输出报告
创建 `code_review/REVIEW_REPORT.md`，包含：
- 发现的问题列表
- 严重程度（高/中/低）
- 修复建议
- 改进优先级

## 参考资料
- scripts/strategies/ 目录
- MEMORY.md 中的技术栈信息

## 时间要求
请在 **2小时内** 输出review报告和技术标准。

## 下一步
发现的问题会交给 Code Agent 修复。

---

CEO 龙虾
