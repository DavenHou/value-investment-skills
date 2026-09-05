# 基本面退出监控输出结构

## 1. 一句话结论

第一句话写明证据截止日、基本面状态、估值状态、估值退出阶段、最关键原因和置信度。不得用公司介绍或研究过程开场。

## 2. 状态卡

| 项目 | 结果 |
|---|---|
| 基本面状态 | 成立／减弱／破坏／证据不足 |
| 估值状态 | 安全边际仍在／接近合理／已兑现或偏高／无法可靠估值 |
| 估值退出阶段 | 未触发／提前复核／历史高点区／逼近风险线／风险线复核／确认硬退出 |
| 当前市赚率／口径 | PE_TTM／ROE_TTM／PR_TTM；同截止日、股份、会计口径；或周期归一化PB路径 |
| 个股历史峰值锚 | `H`；样本轮数；置信度 |
| 提前复核线／市场风险复核线 | `S`／`E`（港股／H股`0.80`；其他基础`1.00`） |
| 安全边际强度 | 强／中／薄／无／未知 |
| 最关键触发项 |  |
| 动作边界 | 允许继续研究／暂停加仓／开始分批兑现／加快减仓／硬退出／立即风险复核 |
| 减弱情景损失 |  |
| 破坏情景损失 |  |
| 复查紧迫度 | 正常／提高／立即 |
| 置信度 | 高／中／低 |
| 下次复核 | 日期、报告或事件 |

动作边界不是自动交易指令。若基本面和估值给出不同信号，分别说明。

## 3. 历轮高点与估值退出阶梯

对已持有资产必须先展示历史样本：

| 轮次 | 峰值日期 | 峰值价格 | 当时可得盈利／净资产与ROE | PR口径 | 峰值PR | 后12月最大回撤 | 数据质量 |
|---|---|---:|---|---|---:|---:|---|
|  |  |  |  |  |  |  |  |

随后固定报告：峰值平均PR、峰值中位PR、变异系数、低于市场风险线的峰值比例、`pre_hard_exit_peak_risk`、市场风险复核线`E`、个股锚 `H`、提前线 `S`、样本限制与置信度。`H`不再被`E`机械封顶。

分批表使用同一PR口径：

| 阶段 | 触发PR | 对应价格 | 累计减仓 | 已执行 | 本档待执行 | 状态／条件 |
|---|---:|---:|---:|---:|---:|---|
| 提前兑现 | `S` |  | 10%–15% |  |  | 公司历史、最新盈利和基本面复核后执行，否则只复核／暂停加仓 |
| 历史高点区 | `H` |  | 30%–40% |  |  | 最新同口径盈利和基本面复核后执行 |
| 确认加速线 | `M`，仅`H<E` |  | 50%–70% |  |  | 历史与基本面共同确认；`H≥E`时不适用 |
| 市场风险线 | `E` |  | 不单独规定 |  |  | 进入`hard_exit_review`，不得只凭PR清仓 |
| 确认硬退出 | 基本面破坏，或风险线、公司历史与最新盈利共同确认明显高估 |  | 80%–100% |  |  |  |
| 确认高估后继续上涨 | 逐档 |  | 剩余仓位的25%–50% |  |  | 每次刷新同口径估值 |

同时说明本次PR变化来自股价、盈利／ROE、股份数还是口径变化。若由盈利或ROE恶化推动，必须同时升级基本面复核。

## 4. 核心断言检查

| 核心断言 | 基线 | 最新证据 | 偏差 | 状态 | 来源与期间 |
|---|---|---|---|---|---|
|  |  |  |  | 支持／待确认／证伪 |  |

只保留决定投资逻辑的三至五项。

## 5. 已触发事项

按严重度排列：硬红旗、核心触发器、软触发器。对每项给出预设阈值、实际结果、是否处于确认期，以及升级或解除条件。

## 6. 压力情景

| 情景 | 盈利／净资产假设 | ROE或利润率 | 估值假设 | 压力价格 | 相对当前损失 |
|---|---:|---:|---:|---:|---:|
| 减弱 |  |  |  |  |  |
| 破坏 |  |  |  |  |  |

显著标明压力价格不是止损价。不能可靠量化时写区间、未知项和可能的跳空风险。

## 7. 过程与证据质量

说明采用的报告期、可比口径、数据来源、是否经过审计、管理层解释是否得到现金流或外部证据支持，以及仍缺少什么。

## 8. 后续动作与复核触发器

列出下一步需要取得的证据、负责人或数据来源、截止时间，以及状态恢复或继续恶化的判定条件。

## 9. 向仓位控制skill交接

最后提供固定字段：

```yaml
position_handoff:
  schema_version: "1.2"
  evidence_cutoff: YYYY-MM-DD
  security:
  currency:
  current_price:
  current_price_date: YYYY-MM-DD
  upstream_gates:
    research_status: pass | conditional | fail | insufficient | missing
    forecast_status: usable | conditional | unusable | non_actionable | missing
    valuation_status: valid | conditional | invalid | non_actionable | missing
    pipeline_status: pass | stopped
    stopped_at:
    remediation_requirements: []
  fundamental_status: intact | weakened | broken | insufficient
  fundamental_reason:
  valuation_status: margin_present | near_fair | realized_or_high | unpriceable
  valuation_exit:
    stage: below_start | early_exit | historical_peak_zone | approaching_hard_exit | hard_exit_review | hard_exit | unpriceable
    action: hold | pause_additions | begin_reduction | accelerate_reduction | hard_exit | evidence_review
    pr_basis:
    current_pr:
    ttm_pairing_status: aligned | conditional | invalid | not_applicable
    pr_change_driver: price | earnings_or_roe | share_count | methodology | mixed
    historical_window:
    valid_peak_cycles:
    peak_mean_pr:
    peak_median_pr:
    peak_cv_percent:
    below_market_risk_line_peak_ratio_percent:
    pre_hard_exit_peak_risk: true | false | unknown
    historical_anchor_h:
    early_exit_s:
    midpoint_m:
    market_risk_review_pr: 1.00 | 0.80
    market_pr_factor: 1.00 | 0.80
    planned_position_basis_shares:
    cumulative_reduction_target_percent:
    cumulative_reduction_completed_percent:
    remaining_position_policy:
    latest_disposal_date:
    threshold_prices:
      early_exit_s_price:
      historical_anchor_h_price:
      midpoint_m_price:
      market_risk_review_price:
    next_rerating_trigger:
    valuation_confirmation: history_and_fundamentals_confirmed | review_required | insufficient
    independent_model_price_low:
    independent_model_price_high:
    sample_confidence: high | medium | low | insufficient
    comparability_gaps: []
  margin_strength: strong | moderate | thin | none | unknown
  confidence: high | medium | low
  add_permission: allowed | paused | prohibited
  review_urgency: normal | elevated | immediate
  hard_cap_reason:
  loss_basis: current_market_price
  stress_cases:
    weakened:
      earnings_or_book_assumption:
      roe_or_margin_assumption:
      valuation_assumption:
      stress_price_low:
      stress_price_high:
      loss_low_percent:
      loss_high_percent:
      horizon:
      gap_risk:
    broken:
      earnings_or_book_assumption:
      roe_or_margin_assumption:
      valuation_assumption:
      stress_price_low:
      stress_price_high:
      loss_low_percent:
      loss_high_percent:
      horizon:
      gap_risk:
  next_review_trigger:
```

未知字段留空并解释，不能用未经证实的数字补齐。`margin_strength` 是估值安全边际的强弱，不是公司质量评分。`hard_cap_reason` 只记录会限制仓位的事实，例如治理事件、流动性或无法估值；行业集中度、组合相关性和用户风险预算由仓位控制skill补充。
