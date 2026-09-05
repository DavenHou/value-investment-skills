# 公司背景档案输出模板

使用短结论优先、证据紧随主张的写法。每个关键事实在正文就近附 Markdown 链接；不要把链接集中堆到文末。

```markdown
# [公司] 背景查询｜截至 [日期]

## 范围与结论
- 主体/市场/范围：
- 最强证据：
- 最关键的反证或风险：
- 尚不能回答的问题：

## 证据状态总览
| 主题 | 当前判断 | 状态 | 关键证据 | 下一步 |
|---|---|---|---|---|

状态只可用：`已证实`、`合理推断`、`待验证`、`相互矛盾`。

## 100分质量评分
| 维度 | 权重 | 得分 | 关键证据与计算期 | 主要反证/缺口 |
|---|---:|---:|---|---|
| 护城河与客户价值 | 20 |  |  |  |
| 增长质量、创新与再投资跑道 | 15 |  |  |  |
| 单位经济、现金流与财务韧性 | 15 |  |  |  |
| 管理层、股东股本与少数股东公平 | 10 |  |  |  |
| 资本配置与股东回报 | 20 |  |  |  |
| 盈利真实性与信息披露 | 10 |  |  |  |
| 风险韧性 | 10 |  |  |  |
| **原始总分** | **100** |  |  |  |

- 评分状态：`90–100 跨周期标杆` / `75–89 强` / `60–74 及格，进入下一轮尽调` / `40–59 偏弱` / `<40 失格`。
- 当前经营恶化触发项：`[逐项列出0–4项及计算期；若无则写无]`。
- 最终分：`[原始分]`；上限/否决闸门：`[如无则写无]`；置信度：`高/中/低`。
- 分红、净回购、降杠杆和高回报再投资都可构成股东回报；不得把高股息率或大额回购金额直接当成高分。
- 非金融企业追加：`确定下限覆盖率 / 严格净金融资产覆盖率 / 严格基础分S / 下限额外分B / 现金覆盖子项（0–5）`；按30%中点的双叶片连续曲线计算并保留到0.1分。将任何待拆分、受限或有重大本金风险的资产明确列出；覆盖率为区间时列出现金分区间，但最终总分只采用已核实低端，不得把上界或主观中点当最终得分。

治理维度必须追加下表；五项合计计入治理10分中的5分，不额外增加100分总分：

| 股东股本子项 | 分值 | 已核实的权利／行为证据 | 主要反证或缺口 |
|---|---:|---|---|
| 最终受益人与控制权清晰度 | /1 |  |  |
| 关键股东利益一致性 | /1 |  |  |
| 决策权、否决权与僵局风险 | /1 |  |  |
| 公司自主性与关联方边界 | /1 |  |  |
| 股本权利与少数股东保护 | /1 |  |  |
| **股东股本结构合计** | **/5** |  |  |

- 另列：`股权结构状态：pass / weak / fail / insufficient`；`最终受益人`；`经济权与投票权差异`；`关键股东协议／保留事项是否可核实`；`股东股本红旗`。

纯科技或混合平台追加，并先显示业务模型分类：`full_technology / hybrid_platform / industry_company`。

| 科技／平台附加闸门 | 得分（0–5） | 一级证据 | 独立交叉证据 | 最强反证 | 状态 |
|---|---:|---|---|---|---|
| 不可替代性 |  |  |  |  | pass / fail / insufficient |
| 可持续成长性 |  |  |  |  | pass / fail / insufficient |
| 自主议价能力 |  |  |  |  | pass / fail / insufficient |

- 纯科技闸门总分：`[x.x]/15`；混合平台只对不可替代性和自主议价能力执行附加门槛，成长性回到行业指标；最终状态：`pass / conditional / fail / insufficient / not_applicable`。
- 该表不增加100分总分。旧报告缺少结构化字段但正文已经有充分的同类证据时可以沿用精确总分并标明待补字段；证据缺失时必须补充复核。

## 公司身份与时间线
| 日期 | 事件 | 对业务/资本/治理的意义 | 证据 |
|---|---|---|---|

## 业务、产品与增长机制
- 客户、产品、变现、渠道和关键经营指标：
- 最近变化及驱动拆解：
- 经营真实性的外部验证：

## 行业、竞争与外部约束
- 行业周期、竞争、替代品、监管与集中度：

## 管理层、股东与资本运作
- 管理层履历、激励与承诺兑现：
- 主要股东、内部人交易、债务/并购/关联方：

## 红旗、反证与资料缺口
| 事项 | 为什么重要 | 目前证据 | 验证动作 | 优先级 |
|---|---|---|---|---|

## 线下/外部核验计划（如适用）
- 核验的核心假设：
- 需要用户确认：城市/样本门店或渠道/时间/预算或授权：
- 样本与观察方法：
- 合规边界与局限：

## 来源
- 仅列正文已使用的关键一级或交叉验证来源，并标注发布日期/数据期。
```

完成前检查：公司身份无歧义；所有关键数字有来源与日期；事实和推断分开；至少说明一个反证；每个评分维度均有来源、计算期和反证；未执行的线下动作未被写成事实；列出可能改变结论的资料缺口。

用于后续投资流水线时，最后追加：

```yaml
research_handoff:
  schema_version: "1.2"
  evidence_cutoff: YYYY-MM-DD
  company:
  security:
  research_status: pass | conditional | fail | insufficient
  final_score:
  evidence_coverage_percent:
  minimum_dimension_pass: true | false
  veto_flags: []
  operating_deterioration_triggers: []
  confidence: high | medium | low
  shareholder_cap_table:
    ultimate_controller:
    ownership_clarity_score:
    interest_alignment_score:
    decision_deadlock_score:
    corporate_autonomy_score:
    minority_rights_score:
    total_score:
    status: pass | weak | fail | insufficient
    red_flags: []
  technology_gate:
    business_model_class: full_technology | hybrid_platform | industry_company
    applicability: full | hybrid | not_applicable
    irreplaceability_score:
    sustainable_growth_score:
    autonomous_pricing_power_score:
    total_score:
    status: pass | conditional | fail | insufficient | not_applicable
    evidence_cutoff:
    disqualifiers: []
  eligible_next_step: earnings_forecast | remediation_only
  remediation_requirements: []
```

`research_status`只能按评分卡闸门生成，不能因估值便宜、股价上涨或用户希望继续而改成`pass`。
