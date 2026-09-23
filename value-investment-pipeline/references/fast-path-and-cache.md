# 快速模式与公司缓存

本参考用于减少重复检索、重复推理和重复计算。目标是把首次研究保留为完整流水线，把日常查询变成变化检查和价格敏感字段刷新。缓存是正式交接的索引，不是证据本身；每个关键字段仍需保留来源URL、公告编号或申报标识与证据截止日。

## 1. 缓存位置与身份

默认路径：

```text
<项目工作目录>/.value-investment-cache/<市场>-<证券代码>.json
```

这是`full`缓存。`quick_valuation`另存，不覆盖它：每次快算把本次实际交付的“核心决策卡＋估值价格带”保存为`screening-output/quick-valuations/<市场>-<证券代码>-<价格日期>.md`；可复用的快算机器缓存单独放在`.value-investment-cache/quick/<市场>-<证券代码>.json`。同一价格日期的修订更新对应文稿并注明修订原因；多证券各存一份。

同一公司不同股份类别分别保存，例如A股与H股不能共用价格、税务和流动性字段；允许在`company_identity`下共享同一法定主体标识。文件使用UTF-8 JSON，更新时先写临时文件、验证后原子替换，避免中断导致半份缓存。

不得缓存财报全文、网页长摘录或推理过程，只保留最小字段、数值口径、来源指纹和失效条件。

## 2. 最小缓存结构

```json
{
  "schema_version": "1.4",
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
    "bull_roe_percent": null,
    "bear_roe_percent": null,
    "neutral_roa_percent": null,
    "bull_roa_percent": null,
    "bear_roa_percent": null,
    "source_fingerprints": []
  },
  "valuation_handoff": {
    "status": "valid",
    "calculated_at": "YYYY-MM-DD",
    "valuation_model_version": "ttm-pr-cutoff-locked-v6",
    "company_type": "stable",
    "cycle_anchor_policy_version": null,
    "cycle_anchor_conflict_status": "not_applicable",
    "pb": null,
    "current_run_rate_roe_percent": null,
    "neutral_roe_percent": null,
    "bear_roe_percent": null,
    "forecast_tier": null,
    "major_earnings_decline_status": null,
    "market_pr_policy_version": "hk-dynamic-c-both-sides-v1",
    "dividend_yield_percent": null,
    "dividend_tax_percent": null,
    "market_coefficient_c": null,
    "ttm_period_end": "YYYY-MM-DD",
    "ttm_diluted_eps": null,
    "pe_ttm": null,
    "roe_ttm_percent": null,
    "pr_ttm": null,
    "decision_roe_percent": null,
    "decision_pr": null,
    "calculation_basis_id": "",
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
    "exit_policy_version": "historical-h-uncapped-v2",
    "fundamental_status": "intact",
    "add_permission": "allowed",
    "evidence_cutoff": "YYYY-MM-DD",
    "historical_peak_pr_sample_count": null,
    "historical_peak_pr_average": null,
    "historical_peak_pr_median": null,
    "early_exit_multiplier": 0.85,
    "historical_h": null,
    "historical_s": null,
    "historical_m": null,
    "market_risk_review_pr": 1.00,
    "threshold_prices": {
      "S": null,
      "H": null,
      "M": null,
      "E": null
    },
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
  "position_handoff": {
    "schema_version": "1.7",
    "executable_percent_now": null,
    "conditional_initial_percent": null,
    "valuation_supported_cumulative_percent": null,
    "portfolio_risk_budget_status": "not_selected_sensitivity_only",
    "max_completed_position_drawdown_percent": 50.0,
    "completed_ladder_drawdown_status": "not_calculated",
    "stock_count_assessment": "unknown",
    "unallocated_capital_policy": "hold_cash_do_not_fill_to_minimum"
  },
  "invalidation_triggers": [],
  "updated_at": "YYYY-MM-DD"
}
```

缓存按本次请求范围校验。完整流水线缺少正式质量分、评分来源、预测状态或估值状态时，不能进入可执行快速模式；`quick_valuation`不读取质量、背景、同业或仓位交接，但估值结论本身不因此获得建仓许可。

快算重访时先按`--scope quick_valuation`校验同证券的`full`缓存；不命中再校验快算专用JSON。两者均不能跳过本次官方披露与价格检查；仅有旧文稿、或最新文稿比JSON更新时，先把文稿作为历史快算版本读取并重建变化字段，不得直接读成当前有效结论。完整模式只读取`full`缓存，快算专用JSON不得解锁质量与仓位。

缓存生产端必须使用上表字段名，不得把`base_eps_path`替代`base_eps`、把`ttm_pr`替代`pr_ttm`。`pr_ttm`是核验项；价格带、快速刷新和退出映射只使用`decision_pr`。`calculation_basis_id`、`ttm_period_end`或价格日缺失时不得快速刷新。不得把`E`混入`H`公式。允许另外保留路径或明细字段，但最小字段仍须齐全。`H=min(峰值平均PR,峰值中位PR)`；`E`是独立市场风险线；仅`H<E`时生成`M=(H+E)/2`。

周期股的`cycle_anchor_policy_version`必须为`cycle-anchor-conflict-v1`，并保存`aligned／material_gap／regime_split`之一；缺失、旧版本或`insufficient`时至少进入`earnings_update`，补齐同日PB、当前弱运行ROE、中性／悲观归一ROE并重算动作许可。非周期股保留`null／not_applicable`。

## 3. 请求范围与刷新深度

请求范围决定运行哪些模块，刷新深度决定这些模块需要重建多少；两者不得混为一谈。`scripts/select_refresh_mode.py --scope`是唯一确定性入口。

| 请求范围 | 保留 | 跳过 |
|---|---|---|
| `quick_valuation`（默认） | 最新财务与TTM、纯现金覆盖、三年熊／基准／牛预测、归一化ROE／ROA、杜邦及盈利能力可靠性、唯一决策PR、市场系数、买入与退出价格、压力与点时一致性检查 | 公司背景、质量评分、同业信号、仓位与组合约束 |
| `full`（仅在用户明确要求完整时） | 全部正式流水线 | 无 |

`quick_valuation`适用于“跑一下”、仅给公司名／代码调用本 skill，以及“快算、只算估值、估值与退出”等请求。它不是只套公式：预测、归一化和估值／退出输入缺失时仍须重建；因跳过质量与仓位，结果默认是估值结论，不是可执行仓位建议。只有“完整跑一下、完整分析、全流程、从头完整研究”等明确完整意图才使用`full`。

正式决策PR与价格带须通过盈利预测交接闸门：调用`company-earnings-forecast`形成三年情景，F1–F3 ROE／ROA必须能由逐年归母利润、平均归母权益／平均总资产的计算桥复算。预测skill给出`usable`交接时，按其模型计算结果纳入估值；不得仅因未来经营与资本路径使用明示情景输入，或快算按范围跳过背景研究，就把已复算的预测ROE／ROA判为“直接假设”。若交接仅有直接填入的ROE、缺少可复算的利润或资产负债表路径，或状态为`conditional／non_actionable／insufficient／unusable`，该快算的归一化盈利能力、决策PR与目标价格一律标`insufficient`；不得以临时估值或“条件估算”填入正式价格带。保留可核验的TTM事实与比率，并在固定模板“判断”单元格说明缺口。

执行范围与展示范围分开：`quick_valuation`仍完成上表“保留”列的内部计算，但默认答复严格只有两部分：**核心决策卡**与**估值价格带**。不得另起三年预测、纯现金覆盖、杜邦、压力测试、历史峰值样本、复核触发器或来源章节；用户明确要求展开时才显示。若缺口会使决策PR或价格带失效，只写入固定模板中最相关的“判断”单元格，不展开计算过程、另起章节或新增行。来源链接同样就近放入相关“判断”单元格，不单列来源表。

刷新深度沿用原三档：

| 模式 | 触发条件 | 必做 | 跳过 |
|---|---|---|---|
| `quick_refresh` | 所选范围内无新基本面披露且正式交接有效 | 官方变化检查；刷新范围内的价格／汇率；重算价格敏感字段 | 不重建仍有效的正式交接 |
| `earnings_update` | 新财报、盈利预告、TTM窗口滚动，或预测／估值失效 | 更新所选范围内的财务、预测、归一化、估值、退出与压力字段 | 不运行范围外模块 |
| `full_rebuild` | 首次、缓存无效、身份或股份权利变化、重大事件 | 从头重建所选范围 | 不运行范围外模块 |

### 运行前输出闸门

在选择模式后、写任何统计或用户固定格式前，依次完成：

1. 用官方披露目录取得估值日当时可得的最新申报标识，并传给`select_refresh_mode.py --latest-filing-id`；
2. 刷新范围内的目标证券、必要汇率；仅`full`刷新同业；记录实际价格日期；
3. 审计范围内字段是否来自同一证券、期间、股份数和GAAP／调整后口径，且来源与截止日仍有效；
4. 若第1至3步任一项失败，先运行选择出的重建范围，写回并重新验证缓存；只有验证通过才输出完整决策卡。

快速模式仍必须查询官方披露目录，不能仅因缓存文件日期较新就假设没有新公告。它可以复用有效的正式交接，但不能跳过前述输出闸门；任何过期或不完整字段都必须刷新／重算后才进入全部统计。

历史`--as-of`运行还有一道硬闸门：预测证据截止日、TTM截止日、价格日和退出证据截止日均不得晚于估值日。出现未来日期时必须重建点时输入，不得把负数“资料年龄”当作缓存新鲜，也不得使用后来分红生成的复权价回填历史PB。

## 4. 更新周期与立即失效

| 模块 | 正常复用周期 | 立即失效事件 |
|---|---|---|
| 公司身份／商业模式／质量评分 | 最长370天 | 控制权、审计意见、重大处罚、核心业务或股份权利变化 |
| 盈利预测与归一化ROE／ROA | 至下一份正式业绩材料；无核验最长130天 | 季报／中报／年报、盈利预告、重大并购处置、产能或指引突变 |
| 估值静态参数与压力情景 | 与预测同步 | 新盈利、TTM报告期、股份数、平均权益方法、股息率跨越预测选档边界、重大业绩下滑保护状态变化、稳定企业三年ROE稳定性、周期股盈利锚冲突状态、ROE超过40%触发或复核状态、杜邦杠杆状态、分红／回购、税务、上市结构或市场PR政策变化；缓存缺少高ROE复核状态、周期股缺少`cycle-anchor-conflict-v1`，或港股缺少`hk-dynamic-c-both-sides-v1`及股息率／税率／`c`立即失效 |
| 当前价格／汇率 | 一个交易日 | 每次用户要求“现在”或“最新” |
| 同业价格信号 | 一个交易日 | 弱势组创新低、行业广度变化20个百分点、目标股穿越估值边界 |
| 同业名单 | 180天 | 主营结构、上市状态、重大公司特有事件导致不可比 |

时间上限不是自动通过。到期先做官方变化检查；出现冲突或来源不可访问时标记`partial／invalid`，不得静默沿用。

## 5. 最小联网和Token预算

`quick_refresh`按所选范围工作。`quick_valuation`依次执行：

1. 一次官方披露目录／IR变化检查；
2. 一次目标股与必要汇率请求，并更新纯现金覆盖；
3. 读取或重建三年预测与归一化ROE／ROA，再由本地脚本重算同口径TTM市赚率、决策PR和买卖价格；
4. 只打开发生变化模块对应的来源与参考文件；
5. 默认只输出核心决策卡与估值价格带，不重复内部预测、现金、杜邦、压力、历史样本、复核触发器、来源表或公式。

目标是让范围外模块零检索、范围内正式交接尽量复用，并以一次本地确定性计算收口；预测或归一化失效时仍需读取足够的一手财务材料，不为节省Token沿用旧结论。

## 6. 写回与审计

每次运行记录：

- `mode`、`official_change_check_at`；
- 哪些模块复用、哪些模块刷新；
- 基本面截止日与价格日期；
- 最新公告标识和来源指纹；
- 新的失效触发器；
- 结论是否变化及原因。

更新单个模块时保留其他模块原截止日。新价格只能更新`price_snapshot`和价格敏感结果，不能把`research_handoff.evidence_cutoff`或`forecast_handoff.evidence_cutoff`改成当天。

写回时先生成同目录临时JSON，再用`scripts/select_refresh_mode.py`传入本次官方最新申报标识进行校验。只有返回`cache_status: hit`才原子替换正式缓存；`partial／invalid`不得写回为可复用缓存。这样缓存生产和刷新选择使用同一个校验器，不再各自维护一套字段判断。

`quick_valuation`每次完成后先保存独立Markdown快照，包括证券、基本面与价格截止日、事实来源、预测假设及文稿状态。已完整交付、口径和假设写明的快算结果标`快算定稿`；缺字段或中止的标`未完成`，缺项写`insufficient`，不补造价格带。**快算定稿是截至指定日期的文稿版本，不等于可执行买卖指令，也不等于机器缓存`hit`**；不要仅因跳过质量和仓位就降为“未定稿”。快照沿用[固定快算模板](user-company-query-format.md)，不另造格式。仅当快算所需交接齐全、使用当前官方申报标识以`--scope quick_valuation --cache <快算专用临时JSON>`复核返回`hit`时，才原子替换可复用快算JSON；否则保留快算文稿并注明机器缓存未通过，不覆盖`full`缓存。交付时给出保存路径。
