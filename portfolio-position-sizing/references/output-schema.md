# 仓位控制输出结构

## 1. 一句话结论

第一句话必须写明：当前是否建仓、估值位置、首仓价格与比例、最终累计建议、状态或风险限制，以及证据日期。

## 2. 决策卡

| 项目 | 结果 |
|---|---|
| 流水线状态 | 全部通过／停止于背景／预测／估值／退出监控 |
| 新增／加仓许可 | 允许／暂停／禁止／不可判断 |
| 当前动作 | 建仓／等待／停止加仓／退出评估 |
| 当前估值位置 |  |
| 当前市赚率／对应估值档 |  |
| PE_TTM／ROE_TTM配对口径 | 截止日、股份、GAAP／调整后、平均权益方法 |
| 杜邦／杠杆闸门 | ROE主驱动、权益乘数变化、正常杠杆重算 |
| 三年ROE稳定性／高ROE财技复核 | 稳定股的三年等权平均、CV、可比性；ROE>40%时的可靠性与ROA／ROIC／FCF |
| 中性／悲观PR与差距 |  |
| 中性／悲观决策权重 |  |
| 行业宏观分／证据日期 |  |
| 决策PR／对应估值档 |  |
| PR候选累计仓位／估值支持仓位 |  |
| 本次新增仓位 |  |
| 首仓区间与比例 |  |
| 加仓区间与累计仓位 |  |
| 估值驱动最终建议 |  |
| 采用情景 | 减弱／破坏／用户指定 |
| 用户风险预算 | 组合净值的 % 与金额 |
| 压力损失率 | 低端–高端 |
| 保守风险公式上限 |  |
| 最终可执行上限 |  |
| 单股／持仓数约束 | ≤35%；常态5–8只；当前合格低估候选数 |
| 上市市场／偏好系数 | 美股／A股／港股与实际校准系数 |
| 当前仓位 |  |
| 当前压力损失 | 组合净值的 % 与金额 |
| 分批压力损失 | 已成交档路径损失；完整阶梯加权成本、价格损失及组合损失；未成交档跳空风险 |
| 最终瓶颈 | 状态闸门／风险预算／单股／行业／相关组／流动性／账户限制 |
| 置信度与复查 | 当前信息风险首仓；具体日期、时间、时区；日历／官方披露／价格触发；拟解锁层级；跳空后动作 |

仓位上限不是建议仓位，也不是必须买满的目标。

## 3. 建仓阶梯

本节必须位于公式之前：

| 层级 | 价格／估值区间 | 对应市赚率 | 较当前价格变动 | 本档新增仓位 | 累计仓位 | 基本面解锁条件 | 当前是否执行 |
|---|---:|---:|---:|---:|---:|---|---|
| 首仓 |  |  |  |  |  |  |  |
| 主要加仓 |  |  |  |  |  |  |  |
| 深度价值 |  |  |  |  |  |  |  |
| 极端错价集中 |  |  |  |  |  |  |  |

市赚率必须与价格带使用同一盈利、ROE、股份和预测年度。成长股或平台公司使用预测市赚率时标注“情景辅助”；无法可靠计算时写“不适用／不足”，不得省略。

在本表之前增加仓位形成桥：

| PR候选累计仓位 | 估值支持累计仓位 | 从当前持仓本次新增 | 压力风险上限 | 其他组合上限 | 最终采用／主要瓶颈 |
|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |

状态暂停时仍填写该表，但“当前是否执行”全部为否，并在表前写明当前建议仓位0%。

## 4. 公式与约束

逐项展示风险仓位上限及每个有效上限，不得只给最终数字：

| 约束 | 输入 | 计算上限 | 数据性质 | 是否成为瓶颈 |
|---|---:|---:|---|---|
| 压力风险预算 |  |  | 用户偏好＋模型情景 |  |
| 单一公司 |  |  | 用户规则 |  |
| 行业／主题 |  |  | 组合事实＋用户规则 |  |
| 相关资产组 |  |  | 组合事实＋用户规则 |  |
| 流动性 |  |  | 市场事实＋用户规则 |  |
| 账户／监管 |  |  | 外部约束 |  |

## 5. 压力情景敏感性

分别列出减弱与破坏情景的压力损失、当前组合损失和公式上限。保守可执行值采用所选情景的高损失端；低损失端只能称为敏感性。

## 6. 当前持仓与分批计划

若允许新增，给出剩余额度；只有用户提供或确认分批条件后才输出具体分档。每个分批计划都必须并列展示：已成交档至破坏价的组合损失、假设全部已成交时的现金配置加权平均成本与组合损失、以及下方档位未成交即跳空至破坏价的风险。若暂停或禁止，写明恢复许可所需证据，不生成“越跌越买”档位。

## 7. 缺口与复查触发器

列出缺失的组合净值、风险预算、集中度、相关性、流动性、证据时效或跳空风险。说明哪些缺口使结果不可执行，以及下次重算条件。若唯一缺口是下一期经营确认且完整流水线已通过，明确现在可用的信息风险首仓；若涉及治理、审计、现金归属、偿债、重大客户流失或无法界定的跳空风险，则明确首仓为0%。

另列三触发复核计划：每个尚未解锁的仓位层级分别显示`scheduled_at`、时区、日期状态、复核事件、必查指标和通过后累计仓位。官方未公告时同时列内部检查点和监管最迟／预计窗口；确认后必须列财报前第5个交易日、发布后2小时内或下一常规开盘前、完整报表后的首个用户时区工作日，以及必要时首个完整交易日收盘后的复核。价格穿越市赚率档位或较估值基准价变动默认8%时启动重算，但不自行解锁基本面仓位。

财报后旧价格带自动过期。输出“新基本面通过且新PR仍在档内才加仓；新PR超出档位则保留已有首仓、不追价并取消未执行额度”的跳空动作。

## 8. 机器可读结果

```yaml
position_sizing:
  schema_version: "1.4"
  calculation_date: YYYY-MM-DD
  security:
  currency:
  executable: true | false
  pipeline:
    research_status: pass | conditional | fail | insufficient | missing
    forecast_status: usable | conditional | unusable | non_actionable | missing
    valuation_status: valid | conditional | invalid | non_actionable | missing
    exit_pipeline_status: pass | stopped | missing
    stopped_at:
    remediation_requirements: []
  add_permission: allowed | paused | prohibited | unknown
  current_action: enter | wait | stop_adding | exit_review
  valuation_position:
  valuation_reliability:
    company_history_status: usable | conditional | insufficient
    dupont_roa_status: pass | conditional | fail | insufficient
    key_caveats: []
  dupont_leverage:
    roe_driver: margin | turnover | leverage | mixed | indeterminate
    leverage_review_required: true | false
    stable_three_year_status: strict_stable | relaxed_stable | unstable | unknown | not_applicable
    candidate_scarcity_confirmed: true | false
    relaxed_position_cap_percent: 15
    strict_reconfirmation_reports_required: 2
    extreme_roe_review_required: true | false
    roe_reliability: organic_high_return | usable_with_caution | buyback_or_leverage_distorted | insufficient | not_triggered
    pr_roe_role: primary_path | scenario_auxiliary | diagnostic_only
    normalized_leverage_roe_percent:
  scenario_decision:
    neutral_pr:
    bear_pr:
    divergence_percent:
    industry_macro_score:
    industry_macro_evidence_cutoff:
    final_neutral_weight_percent:
    final_bear_weight_percent:
    decision_pr:
    hard_stress_override:
  position_formation_bridge:
    current_pr:
    current_pr_basis:
    current_pr_valuation_tier:
    pr_candidate_cumulative_percent_low:
    pr_candidate_cumulative_percent_high:
    valuation_supported_cumulative_percent_low:
    valuation_supported_cumulative_percent_high:
    current_add_percent_low:
    current_add_percent_high:
    stress_cap_percent:
    portfolio_cap_percent:
    final_adopted_percent_low:
    final_adopted_percent_high:
    binding_constraint:
  valuation_plan:
    initial_entry:
      price_low:
      price_high:
      pr_low:
      pr_high:
      pr_basis:
      decline_from_current_low_percent:
      decline_from_current_high_percent:
      tranche_percent_low:
      tranche_percent_high:
      cumulative_percent_low:
      cumulative_percent_high:
      unlock_condition:
    add_zone:
      price_low:
      price_high:
      pr_low:
      pr_high:
      pr_basis:
      decline_from_current_low_percent:
      decline_from_current_high_percent:
      tranche_percent_low:
      tranche_percent_high:
      cumulative_percent_low:
      cumulative_percent_high:
      unlock_condition:
    deep_value_zone:
      price_low:
      price_high:
      pr_low:
      pr_high:
      pr_basis:
      decline_from_current_low_percent:
      decline_from_current_high_percent:
      tranche_percent_low:
      tranche_percent_high:
      cumulative_percent_low:
      cumulative_percent_high:
      unlock_condition:
    extreme_mispricing_zone:
      price_low:
      price_high:
      pr_low:
      pr_high:
      pr_basis:
      decline_from_current_low_percent:
      decline_from_current_high_percent:
      tranche_percent_low:
      tranche_percent_high:
      cumulative_percent_low:
      cumulative_percent_high:
      unlock_condition:
  valuation_suggested_cap_percent:
  selected_stress_case: weakened | broken | user_defined
  risk_budget_percent:
  risk_budget_amount:
  stress_loss_low_percent:
  stress_loss_high_percent:
  conservative_formula_cap_percent:
  sensitivity_formula_cap_percent:
  effective_cap_percent:
  effective_cap_amount:
  current_weight_percent:
  current_stress_loss_percent_of_portfolio:
  current_stress_loss_amount:
  remaining_capacity_percent:
  binding_constraint:
  current_stock_count:
  qualified_undervalued_count:
  preferred_stock_count_low: 5
  preferred_stock_count_target: 6
  preferred_stock_count_high: 8
  stock_count_policy: opportunity_driven
  listing_market:
  market_preference_factor:
  maximum_single_stock_percent: 35
  tranche_stress:
    completed_tranches: []
    stress_price_low:
    stress_price_high:
    completed_ladder_weighted_average_cost:
    completed_ladder_loss_percent:
    completed_ladder_loss_percent_of_portfolio:
    unfilled_tranche_gap_risk: true
  current_information_risk_tranche:
    eligible: true | false
    percent_low:
    percent_high:
    rationale:
    blocking_risks: []
  unlocked_only_after_full_review_percent:
  unresolved_constraints: []
  next_review:
    scheduled_at:
    timezone:
    date_status: official_confirmed | regulatory_latest | estimated_window | internal_checkpoint | event_driven
    event:
    target_cumulative_percent:
    required_metrics: []
    source:
  next_review_trigger:
  review_plan:
    timezone:
    baseline_price:
    baseline_price_date:
    calendar_triggers:
      - phase: current_decision | pre_earnings | release_fast_review | full_filing_review | post_gap_close
        scheduled_at:
        date_status: official_confirmed | regulatory_latest | estimated_window | internal_checkpoint
        target_cumulative_percent:
        required_metrics: []
    disclosure_triggers: []
    price_triggers:
      tier_crossing_prices: []
      stale_move_percent: 8
      rule: revalue_only_not_position_unlock
    gap_up_action:
      add_if:
      do_not_chase_if:
      old_price_band_status: invalid_after_new_results
    automation_created: true | false
    monitoring_handoff:
      baseline_date:
      exact_target_weights: []
      exact_price_triggers: []
      official_sources: []
      last_successful_check_at:
      consecutive_failure_count:
      deduplication_keys: []
      notification_destination:
      order_execution_allowed: false
```

未知值留空，不能用默认值伪装成用户已确认的风险偏好。
