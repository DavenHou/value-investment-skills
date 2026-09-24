# 价值投资 Skills

面向 A 股、港股与美股的中文价值投资研究 skills。每项研究坚持来源可追溯、会计口径一致、事实与情景假设分离，并且不执行交易。

## 已包含的 skills

- `company-background-research`：公司背景、治理与质量研究。
- `company-earnings-forecast`：三年熊市／基准／乐观经营预测。
- `company-valuation-calculation`：同口径 PE／ROE 市赚率、杜邦与资本结构复核。
- `fundamental-exit-monitoring`：基本面与估值兑现退出规则。
- `portfolio-position-sizing`：条件价格带、压力损失和组合仓位约束。
- `pure-cash-coverage`：现金与严格净金融资产覆盖率。
- `value-investment-pipeline`：串联上述模块的一键研究流程。

## 版本边界

可复用的方法、说明、脚本和测试保留在各 skill 目录。[研究归档](研究归档/README.md)保存按日期冻结的公司快算、综合报告、筛选数据和历史缓存快照，便于追溯；这些快照不是最新估值，也不作为运行时可复用缓存。运行时的 `screening-output/` 与 `.value-investment-cache/` 仍留在本地并被 Git 忽略。

每次更新规则请记录证据截止日、口径变更和对下游模块的影响。重新评估公司时，应重新核验最新公告、价格与缓存有效性。

## 免责声明

内容用于研究和教育，不构成证券买卖建议或交易指令。
