# 估值计算输出结构

以下顺序为硬性要求。第1—3节属于“结论区”，必须在任何公式、输入明细或研究过程之前完整输出；第4节开始才进入“计算过程”。

## 1. 一句话结论

第一句话直接回答“当前处于什么估值位置”。句中至少包含估值截止日、当前价格、基础／修正PR及区间判断。不要以公司介绍、数据来源、方法说明或免责声明开场。

示意：`截至[日期]，[公司]现价[价格]，修正PR为[数值]，处于[经验区间位置]；在[核心假设]下，[核心观察区间]为[价格范围]。`

## 2. 核心结论卡

紧接一句话结论，用一个紧凑表格或不超过五个要点集中展示：

- 当前价格、同口径`PE_TTM`、`ROE_TTM`、`PR_TTM`，以及中性归一PR与悲观归一PR；
- 稳定非周期企业的最近三年ROE等权平均、变异系数与`strict_stable／relaxed_stable／unstable`分级；受控放宽时显示严格候选数不足、15%仓位限制和重新确认日历；ROE超过40%时的财技复核和ROE可靠性状态；
- 杜邦ROE主驱动、权益乘数变化和杠杆复核状态；
- 中性／悲观差距率、企业类型基础权重、行业宏观分与最终权重、决策PR；
- 框架区间位置，例如深度低估／较有安全边际／低估观察区上沿／名义合理或偏高区；
- 最重要的条件估值价格区间；
- 跨市场时的基础目标PR、市场PR系数、校准后目标PR、价格带及校准原因；
- 市场风险复核线（港股／H股`0.80`；其他基础`1.00`，如适用），并标明它不是机械目标价或单指标清仓线；
- 最大不确定性与结论置信度。

读者只看本节也必须能够知道结果。不得把核心价格区间留到计算过程之后。

## 3. 情景敏感性与判断

先给悲观、中性、乐观三组盈利或ROE情景对应的条件价格区间，再用三至五句话解释为什么当前落在该位置、什么变化会让结论上移或下移。稳定非周期企业中性归一值使用最近三个可比完整财年ROE等权平均与未来三年基准预测；技术／结构性成长企业仍用历史近期加权值与基准预测；周期股中性归一值使用完整周期阶段平衡值与基准预测。悲观归一值使用历史弱年份锚与熊市预测；预测值必须明确标为假设，不得伪装成已确认结果。

在本节末尾使用清晰的过渡句，例如：`以下为数据口径与计算过程。`

## 4. 范围、输入与适用性

列出公司、代码、股份类别、上市地、币种、估值日、报告期。解释为什么选择稳定价值股、周期股、成长股、金融企业或指数路径；不适用的路径也简短说明。

随后列出输入与证据：

| 输入 | 数值 | 日期／期间 | 口径 | 来源 | 质量提示 |
|---|---:|---|---|---|---|
| 当前价格／市值 |  |  | 股份与币种 |  |  |
| PE_TTM或PB |  |  | TTM截止日／年度 |  |  |
| ROE_TTM |  |  | 最近四季利润／五季末季度时间加权权益；两点平均须标注 |  |  |
| 最近三年ROE稳定性 |  |  | 逐年值、等权平均、标准差、变异系数、可比性 |  |  |
| 高ROE财技复核 |  |  | TTM或三年任一ROE>40%；回购、净资产、杠杆、ROA／ROIC／FCF |  |  |
| PE_TTM／ROE_TTM配对 |  |  | 同截止日、股份、GAAP／调整后口径 |  |  |
| 归一化ROE |  |  | 历史预测加权归一化 |  |  |
| ROA |  |  | 与ROE相同年度及权重，仅作杠杆交叉检查 |  |  |
| 盈利能力口径 |  |  | 企业类型、历史窗口、弱年份、当前弱运行率、历史／预测块权重 |  |  |
| 周期分类与阶段 |  |  | 周期驱动、leader／mainstream／high_cost_tail、低谷／复苏／景气／回落及证据 |  |  |
| 周期产业信号 |  |  | deteriorating／mixed／bottoming／recovering／insufficient；与股价择时分开 |  |  |
| 股利支付率 |  |  | 多年平均 |  |  |
| 净回购／股本稀释 |  |  | 多年平均／稀释后股数 |  |  |
| 税后股东回报 |  |  | 投资者实际账户与持有路径 |  |  |
| 税率 |  |  | 投资者与账户假设 |  |  |
| 汇率／流动性 |  |  | 估值日／日均成交和退出天数 |  |  |

每个当前数据必须有直接来源和日期。预测值必须标为假设并链接到预测逻辑。

## 5. 逐式计算

展示代入过程，不只给答案：

```text
基础PR（PE路径） = PE / ROE百分数点 = …
当前PR_TTM = PE_TTM / ROE_TTM百分数点 = …
基础PR（PB路径） = 100 × PB / ROE百分数点² = …
历史悲观ROE锚 = min(弱年份加权ROE, 当前弱运行率) = …
历史悲观ROA锚 = 与所选ROE锚相同来源和期间的ROA = …
稳定非周期企业三年历史中性ROE = (ROE_Y-2 + ROE_Y-1 + ROE_Y) / 3 = …
稳定非周期企业中性归一ROE = 60% × 三年等权平均ROE + 20% × F1 + 12% × F2 + 8% × F3 = …
技术／结构性成长企业中性归一ROE = 历史块权重 × 历史近期加权ROE + F1–F3基准ROE加权值 = …
周期股阶段平衡ROE = mean(低谷阶段均值, 复苏阶段均值, 景气阶段均值, 回落阶段均值) = …
周期股中性归一ROE = 历史块权重 × 周期阶段平衡ROE + F1–F3基准ROE加权值 = …
悲观归一ROE = 历史块权重 × 历史悲观锚 + F1–F3熊市ROE加权值 = …
中性／悲观归一ROA = 与对应ROE相同年度、期间、情景和权重 = …
杠杆放大倍数 = 归一化ROE / 归一化ROA = …
杜邦ROE_TTM = 归母净利率_TTM × 总资产周转率_TTM × 权益乘数_TTM = …
修正系数N = clamp(50 / 多年股利支付率, 1, 2) = …
修正PR = N × 基础PR = …
```

若多条路径结果不一致，展示差额并解释，不能静默平均。同一路径内使用动态情景权重时，另外展示基础权重、差距修正、行业宏观修正和最终权重。

## 6. 价格映射明细

对用户指定或适用的目标PR，列出基础目标PR、市场PR系数、校准后目标PR、目标PE、目标PB和目标价格。周期股必须分别列出中性、悲观两种归一ROE下的公司专属目标PB；至少覆盖基础`0.55／0.50／0.40／0.30`四档及其市场校准值。把基础`0.4／0.5／0.6／1.0／1.5`明确标为来源框架的经验阈值；港股／H股实际动作阈值再乘以`0.80`。`1PB／0.5PB`只能标成特定ROE假设下的速查交叉验证。这里用于展开第2—3节已给出的结果，不能在此首次披露核心价格区间。

## 7. 公司历史、杜邦与ROA可靠性

列出公司自身至少五年、优先十年的同口径滚动`PR_TTM`中位数、25／75分位、当前分位和可比性断点。长期高于或低于1时解释结构原因，不据此机械放宽阈值。

非金融企业追加杜邦表：

| 杜邦因子 | 当前TTM | 3–5年中位数 | 变化 | 对ROE贡献／风险 |
|---|---:|---:|---|---|
| 归母净利率 |  |  |  |  |
| 总资产周转率 |  |  |  |  |
| 权益乘数 |  |  |  |  |

给出`roe_driver`与`leverage_review_required`。当前TTM或最近三年任一ROE超过40%时，再给出`extreme_roe_review_required`、`roe_reliability`、净回购／净资产收缩判断、`ROA_TTM`、三年等权ROA、ROIC和每股FCF趋势。若ROE被回购或杠杆失真，明确写`PR只作诊断`，不得把ROA直接代入PR公式。金融企业以监管资本、资产质量、拨备和信用成本替代工业企业杜邦杠杆阈值。

随后完成其他交叉检查：

- 企业质量、治理和盈利真实性；
- 历史估值区间与同行；
- 现金安全垫（非金融企业）；
- 分红、回购、稀释和资本配置；
- 周期属性、公司在成本曲线／行业中的角色和净资产质量；
- 周期产业右侧信号；与同业股票价格择时信号分列；
- 金融企业的行业专属指标；
- 税负、汇率和跨市场价差。

## 8. 风险、缺口与复核触发器

说明哪些输入最敏感、哪些证据缺失，以及什么变化会让估值失效，例如ROE永久下台阶、周期假设错误、分红政策改变、重大增发、资产减值或治理恶化。

最后分别写：

- **可以确认的计算结果**
- **依赖假设的判断**
- **仍不能确认的事项**

不得把估值区间直接写成买入或卖出建议。

用于下游退出监控和仓位控制时，最后追加：

```yaml
valuation_handoff:
  schema_version: "1.4"
  valuation_model_version: ttm-pr-dupont-v4
  evidence_cutoff: YYYY-MM-DD
  security:
  currency:
  current_price:
  current_price_date: YYYY-MM-DD
  upstream_research_status: pass | conditional | fail | insufficient | missing
  upstream_forecast_status: usable | conditional | unusable | non_actionable | missing
  valuation_status: valid | conditional | invalid | non_actionable
  valuation_position: deep_value | margin_present | near_fair | high | unpriceable
  margin_strength: strong | moderate | thin | none | unknown
  ttm_snapshot:
    period_end: YYYY-MM-DD
    accounting_basis: gaap | statutory | adjusted
    pe_ttm:
    roe_ttm_percent:
    roe_average_equity_method: five_quarter_time_weighted | two_point_average | event_date_time_weighted
    pr_ttm:
    single_quarter_annualized: false
    comparability_status: aligned | conditional | invalid
  dupont:
    net_margin_ttm_percent:
    asset_turnover_ttm:
    equity_multiplier_ttm:
    equity_multiplier_history_median:
    roic_ttm_percent:
    net_debt_to_ebitda:
    interest_coverage:
    roe_driver: margin | turnover | leverage | mixed | indeterminate
    leverage_review_required: true | false
    extreme_roe_review_required: true | false
    roe_reliability: organic_high_return | usable_with_caution | buyback_or_leverage_distorted | insufficient | not_triggered
    gross_buyback_vs_net_share_change_status: aligned | offsetting_dilution | equity_shrinking | insufficient | not_applicable
    current_ttm_roa_percent:
    three_year_equal_weight_roa_percent:
    roa_primary_profitability_quality_check: true | false
    pr_roe_role: supporting_model | diagnostic_only
    normalized_leverage_roe_percent:
    caveats: []
  company_history:
    company_pr_ttm_history_years:
    company_pr_ttm_p25:
    company_pr_ttm_median:
    company_pr_ttm_p75:
    current_pr_ttm_percentile:
    historical_comparability_breaks: []
  scenario_decision:
    neutral_pr:
    bear_pr:
    divergence_percent:
    base_neutral_weight_percent:
    base_bear_weight_percent:
    divergence_shift_to_bear_percent_points:
    industry_macro_score: -2 | -1 | 0 | 1 | 2
    industry_macro_evidence_cutoff: YYYY-MM-DD
    industry_macro_shift_to_neutral_percent_points:
    final_neutral_weight_percent:
    final_bear_weight_percent:
    decision_pr:
    hard_stress_override: true | false
    weighting_rationale:
  normalized_profitability:
    company_type: stable | cyclical | technology | financial | index
    historical_years:
    stable_three_year_roe_values: []
    stable_three_year_equal_weight_roe_percent:
    stable_three_year_roe_standard_deviation_points:
    stable_three_year_roe_cv_percent:
    stable_three_year_quantitative_status: strict_stable | relaxed_eligible | unstable | not_applicable
    stable_three_year_qualitative_comparability: confirmed | not_confirmed | unknown | not_applicable
    stable_three_year_tier: strict_stable | relaxed_stable | unstable | not_applicable
    stability_policy: strict | controlled_relaxation
    strict_candidate_count:
    minimum_candidate_count:
    candidate_scarcity_confirmed: true | false
    relaxed_position_cap_percent: 15
    strict_reconfirmation_reports_required: 2
    stable_neutral_anchor_usable: true | false
    historical_selection_rule: weakest_40_percent_minimum_two_years
    historical_selected_years: []
    historical_recent_weighted_roe_percent:
    historical_equal_weighted_roe_percent:
    cycle_phase_status: complete_phase_balanced | provisional_equal_weight | not_applicable
    cycle_phase_labels: []
    cycle_phase_roe_percent:
      trough:
      recovery:
      boom:
      downturn:
    historical_cycle_phase_balanced_roe_percent:
    historical_lower_tail_roe_percent:
    current_weak_roe_percent:
    historical_conservative_roe_anchor_percent:
    historical_recent_weighted_roa_percent:
    historical_equal_weighted_roa_percent:
    cycle_phase_roa_percent:
      trough:
      recovery:
      boom:
      downturn:
    historical_cycle_phase_balanced_roa_percent:
    historical_lower_tail_roa_percent:
    current_weak_roa_percent:
    historical_conservative_roa_anchor_percent:
    forecast_bear_years: 3
    historical_weight_percent:
    forecast_weight_percent:
    normalized_neutral_roe_percent:
    normalized_neutral_roa_percent:
    normalized_bear_roe_percent:
    normalized_bear_roa_percent:
    roe_to_roa_multiplier:
    leverage_review_required: true | false
    forecast_confidence: high | medium | low
  cyclical_assessment:
    applicability: cyclical | not_cyclical | uncertain
    company_role: leader | mainstream | high_cost_tail | uncertain | not_applicable
    cycle_driver:
    asset_quality_status: pass | conditional | fail | insufficient | not_applicable
    cycle_fundamental_signal: deteriorating | mixed | bottoming | recovering | insufficient | not_applicable
    cycle_signal_evidence_cutoff: YYYY-MM-DD
    equity_timing_signal: separate_downstream_field
    neutral_roe_method:
    heuristic_pb_cross_check_only:
  cyclical_pb_bands:
    neutral_pr_0_55_pb:
    bear_pr_0_55_pb:
    neutral_pr_0_50_pb:
    bear_pr_0_50_pb:
    neutral_pr_0_40_pb:
    bear_pr_0_40_pb:
    neutral_pr_0_30_pb:
    bear_pr_0_30_pb:
  bands:
    pr_0_4_price_low:
    pr_0_4_price_high:
    pr_0_5_price_low:
    pr_0_5_price_high:
    pr_0_6_price_low:
    pr_0_6_price_high:
  cross_market:
    listing_market: A_share | Hong_Kong | US | ADS
    market_pr_factor: 1.00 | 0.80
    base_market_risk_review_pr: 1.00
    adjusted_market_risk_review_pr: 1.00 | 0.80
    base_entry_pr_thresholds: [0.55, 0.50, 0.40, 0.30]
    adjusted_entry_pr_thresholds:
    basic_band_low:
    basic_band_high:
    adjusted_band_low:
    adjusted_band_high:
    after_tax_shareholder_yield:
    fx_rate:
    liquidity_haircut_percent:
    market_adjustment_reason:
  bear_eps_or_book_value:
  base_eps_or_book_value:
  bull_eps_or_book_value:
  confidence: high | medium | low
  eligible_next_step: exit_monitoring | remediation_only
  invalidation_triggers: []
```

只有上游背景调查`pass`、业绩预测`usable`、主估值路径输入有效且杜邦／ROA可靠性检查完成时，`valuation_status`才可为`valid`并进入退出监控。
