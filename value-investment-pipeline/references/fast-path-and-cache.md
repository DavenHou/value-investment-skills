# 快速模式与公司缓存

本参考用于减少重复检索、重复推理和重复计算。目标是把首次研究保留为完整流水线，把日常查询变成变化检查和价格敏感字段刷新。缓存是正式交接的索引，不是证据本身；每个关键字段仍需保留来源URL、公告编号或申报标识与证据截止日。

## 1. 缓存位置与身份

默认路径：

```text
<项目工作目录>/.value-investment-cache/<市场>-<证券代码>.json
```

同一公司不同股份类别分别保存，例如A股与H股不能共用价格、税务和流动性字段；允许在`company_identity`下共享同一法定主体标识。文件使用UTF-8 JSON，更新时先写临时文件、验证后原子替换，避免中断导致半份缓存。

不得缓存财报全文、网页长摘录或推理过程，只保留最小字段、数值口径、来源指纹和失效条件。

## 2. 最小缓存结构

```json
{
  "schema_version": "1.2",
  "company_identity": {
    "legal_name": "",
    "security": "",
    "market": "",
    "currency": "",
    "share_class": "",
    "identity_checked_at": "YYYY-MM-DD"
  },
  "research_handoff": {
    "status": "pass",
    "score": 0.0,
    "evidence_coverage_percent": 0.0,
    "confidence": "",
    "evidence_cutoff": "YYYY-MM-DD",
    "source_fingerprints": []
  },
  "forecast_handoff": {
    "status": "usable",
    "latest_filing_id": "",
    "evidence_cutoff": "YYYY-MM-DD",
    "base_eps": null,
    "bear_eps": null,
    "neutral_roe_percent": null,
    "bear_roe_percent": null,
    "neutral_roa_percent": null,
    "bear_roa_percent": null,
    "source_fingerprints": []
  },
  "valuation_handoff": {
    "status": "valid",
    "calculated_at": "YYYY-MM-DD",
    "valuation_model_version": "ttm-pr-dupont-v4",
    "company_type": "stable",
    "market_pr_policy_version": "hk-pr-threshold-0.80-v1",
    "ttm_period_end": "YYYY-MM-DD",
    "pe_ttm": null,
    "roe_ttm_percent": null,
    "pr_ttm": null,
    "roe_average_equity_method": "",
    "dupont_leverage_review_required": false,
    "extreme_roe_review_required": false,
    "roe_reliability": "not_triggered",
    "stable_three_year_status": "strict_stable",
    "candidate_scarcity_confirmed": false,
    "relaxed_position_cap_percent": null,
    "company_pr_history": {},
    "share_count": null,
    "price_bands": {},
    "source_fingerprints": []
  },
  "exit_handoff": {
    "fundamental_status": "intact",
    "add_permission": "allowed",
    "evidence_cutoff": "YYYY-MM-DD",
    "weakened_loss_high_percent": null,
    "broken_loss_high_percent": null
  },
  "peer_timing": {
    "universe": [],
    "universe_checked_at": "YYYY-MM-DD",
    "last_price_date": "YYYY-MM-DD",
    "status": "unconfirmed"
  },
  "price_snapshot": {
    "price": null,
    "price_date": "YYYY-MM-DD",
    "fx_rate": null,
    "fx_date": null
  },
  "invalidation_triggers": [],
  "updated_at": "YYYY-MM-DD"
}
```

缺少正式质量分、评分来源、预测状态或估值状态时，不能用缓存进入可执行快速模式。

## 3. 三种运行模式

| 模式 | 触发条件 | 必做 | 跳过 |
|---|---|---|---|
| `quick_refresh` | 无新基本面披露，身份与正式交接有效 | 官方变化检查；批量价格／汇率／同业刷新；重算PR、档位、跌幅和当前动作 | 背景重查、重新评分、三年预测、重复压力建模 |
| `earnings_update` | 新财报、盈利预告、TTM窗口滚动，或预测／估值失效 | 更新财务、`PE_TTM／ROE_TTM／PR_TTM`、杜邦、预测、压力与仓位 | 没有治理或业务模式变化时不重跑背景评分 |
| `full_rebuild` | 首次、缓存无效、身份或股份权利变化、重大治理／审计／业务模式事件 | 完整流水线 | 无 |

### 运行前输出闸门

在选择模式后、写任何统计或用户固定格式前，依次完成：

1. 用官方披露目录取得最新申报标识，并传给`select_refresh_mode.py --latest-filing-id`；
2. 刷新目标证券、同业和必要汇率，记录实际价格日期；
3. 审计缓存的预测、估值、退出、压力和仓位字段是否都来自同一证券、期间、股份数和GAAP／调整后口径，且来源与截止日仍有效；
4. 若第1至3步任一项失败，先运行选择出的重建范围，写回并重新验证缓存；只有验证通过才输出完整决策卡。

快速模式仍必须查询官方披露目录，不能仅因缓存文件日期较新就假设没有新公告。它可以复用有效的正式交接，但不能跳过前述输出闸门；任何过期或不完整字段都必须刷新／重算后才进入全部统计。

## 4. 更新周期与立即失效

| 模块 | 正常复用周期 | 立即失效事件 |
|---|---|---|
| 公司身份／商业模式／质量评分 | 最长370天 | 控制权、审计意见、重大处罚、核心业务或股份权利变化 |
| 盈利预测与归一化ROE／ROA | 至下一份正式业绩材料；无核验最长130天 | 季报／中报／年报、盈利预告、重大并购处置、产能或指引突变 |
| 估值静态参数与压力情景 | 与预测同步 | 新盈利、TTM报告期、股份数、平均权益方法、稳定企业三年ROE稳定性、ROE超过40%触发或复核状态、杜邦杠杆状态、分红／回购、税务、上市结构或市场PR政策变化；缓存缺少高ROE复核状态或港股缺少`hk-pr-threshold-0.80-v1`立即失效 |
| 当前价格／汇率 | 一个交易日 | 每次用户要求“现在”或“最新” |
| 同业价格信号 | 一个交易日 | 弱势组创新低、行业广度变化20个百分点、目标股穿越估值边界 |
| 同业名单 | 180天 | 主营结构、上市状态、重大公司特有事件导致不可比 |

时间上限不是自动通过。到期先做官方变化检查；出现冲突或来源不可访问时标记`partial／invalid`，不得静默沿用。

## 5. 最小联网和Token预算

`quick_refresh`按以下顺序工作：

1. 一次官方披露目录／IR变化检查；
2. 一次批量价格请求，覆盖目标股、3–6只同业、行业基准及必要汇率；
3. 本地脚本重算收益、均线、行业广度、同口径TTM市赚率、价格档和跌幅；
4. 只打开发生变化模块对应的来源与参考文件；
5. 默认输出核心结论，不重复公司历史、旧财务表和公式。

目标是把通常的日常查询限制在1–2轮联网、2–4个主要来源和一次本地确定性计算；这是执行目标而非时间保证。若出现新财报、口径冲突或红旗，立即升级模式，不为节省Token继续使用旧结论。

## 6. 写回与审计

每次运行记录：

- `mode`、`official_change_check_at`；
- 哪些模块复用、哪些模块刷新；
- 基本面截止日与价格日期；
- 最新公告标识和来源指纹；
- 新的失效触发器；
- 结论是否变化及原因。

更新单个模块时保留其他模块原截止日。新价格只能更新`price_snapshot`和价格敏感结果，不能把`research_handoff.evidence_cutoff`或`forecast_handoff.evidence_cutoff`改成当天。
