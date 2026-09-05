# 一键价值投资分析输出结构

## 默认：用户公司查询格式

日常公司查询先执行 [公司查询固定格式](user-company-query-format.md)：结论与核心表 → 同业强弱 → 建仓阶梯 → 主要基本面与复核 → 基本面退出 → 估值兑现退出。两类退出内容必须每次出现；缺少历史峰值数据时写 `insufficient`，不得省略。

## 兼容：核心模式

除非用户明确要求展开，否则完整答案按以下七段输出，不再追加后文的详细结构：

1. **一句话结论**：当前动作、首个有效价格区间、当前新增仓位、条件累计上限和最主要限制。
   下一行简写运行模式、缓存命中状态、复用的基本面截止日和最新价格日期；`quick_refresh`不重复公司背景。
2. **公司比较表**：每家公司一行，固定显示当前价格、精确质量分及评分日期、业务模型分类、同口径`PE_TTM／ROE_TTM／PR_TTM`、中性／悲观归一化ROE及ROA、杜邦主驱动／杠杆状态、中性／悲观市赚率及决策PR、估值位置、当前动作和当前新增仓位。质量分和闸门分数继承背景调查正式结果，不得重新评分或输出约数。周期股紧接一张周期专用表，不能把周期阶段、产业信号或目标PB塞进备注省略。
3. **行业同业强弱与领先信号**：只列3–6只代表同业，强／弱角色必须来自基本面和行业地位；另行显示20日与60日相对行业表现、是否先下跌、是否先止跌、龙头是否仍在晚跌、行业广度和当前状态。明确价格跌幅不决定强弱标签，该信号只控制短期首仓节奏。
4. **仓位形成桥**：建仓状态显示当前市赚率支持的累计仓位、本次新增仓位、同业择时约束、压力／组合上限、最终采用值和主要瓶颈。退出状态则显示当前仓位、本档目标剩余仓位、已减与待减、税务／流动性约束和最迟处置日。
5. **条件化建仓或退出阶梯**：未持有或未触发估值退出时显示建仓阶梯；已持有且已触发估值退出时，改为每家公司单独一张退出表，显示历史峰值均值／中位数、个股锚 `H`、提前线 `S`、市场风险复核线`E`（港股／H股`0.80`；其他基础`1.00`）、对应价格、累计减仓目标、已执行与本档待执行。不得把多家公司挤在同一阶梯行。
6. **核心判断**：最多5条，每条一句，优先趋势、估值、行业强弱、治理、安全垫和最大反证。
7. **具体复核日历、触发器与来源**：先列当前信息风险首仓，再列每个尚未解锁仓位的当前决策、财报前预检、发布后快审和完整报表复核时间；同时显示日历／官方披露／价格／同业止跌四类触发器及财报跳空后的加仓或不追价条件，最后附3–5个最主要来源。

### 公司比较表固定格式

| 公司／证券 | 当前价／日期 | 质量分／评分日期 | 业务分类 | PE_TTM／ROE_TTM／PR_TTM | 中性／悲观归一ROE（ROA） | 杜邦主驱动／杠杆复核 | 中性／悲观市赚率；决策PR | 估值位置 | 当前动作 | 当前新增仓位 |
|---|---:|---|---|---|---|---|---|---|---|---:|
|  |  |  |  | 同截止日、股份、会计口径 |  |  |  |  |  |  |  |

- 市赚率不适用或数据不足时写“不适用／不足”，不能省略该列。
- `PE_TTM／ROE_TTM`必须配对并注明GAAP／法定或调整后口径、平均权益方法；完整TTM存在时不得使用单季乘四。
- 使用预测ROE时，在数值后标“情景辅助”；使用股东回报修正时同时显示基础值与修正值。
- 归一化ROE／ROA必须并列显示中性和悲观口径；详细模式再展示历史年数、弱年份、当前弱运行率、历史中性／悲观锚、未来基准／熊市场景三年及块权重。周期股中性历史锚必须标成`阶段平衡／临时逐年等权`，悲观锚标明弱年份；ROA只作杠杆检查。
- ROA先做口径失真检查。利润／资产期间错配、只用期末资产、并购或资产处置、重大融资／A+H发行、重组或会计重述导致分母不可比时，紧接核心表显示“原始ROA、修正ROA、修正公式、修正原因、决策用途”。没有需修正事项时显示“无需修正（沿用X%）”，不得制造调整值。修正ROA不进入PR公式。
- 稳定非周期企业的中性历史锚必须标成“最近三个可比完整财年ROE等权平均”，并显示三年逐年值、标准差、变异系数和定性可比性。当前TTM或三年任一ROE超过40%时，必须显示`extreme_roe_review_required`、`roe_reliability`和ROA／ROIC／FCF判断；确认回购／杠杆失真时PR只作诊断。
- 质量分必须显示为一位小数及证据截止日；来源未能定位时重新运行背景skill。仍无正式分数则写`insufficient`并停止，不输出“约60+”或其他模糊数值。
- 纯科技显示不可替代／成长／议价三项一位小数分数、合计和状态；混合平台显示不可替代／议价两项及行业增长状态；行业公司写`不适用`。旧报告证据充分但字段缺失时标`沿用精确总分／待补字段`，证据不足时停止。

### 周期股专用表（适用时必填）

| 公司／证券 | 周期驱动 | 公司角色 | 四阶段与证据区间 | 阶段平衡中性ROE | 弱年份悲观ROE | 净资产质量 | 产业周期信号／日期 | 股票择时信号／日期 |
|---|---|---|---|---:|---:|---|---|---|
|  | 产品价格／订单／库存／资本开支等 | leader／mainstream／high_cost_tail／uncertain | trough／recovery／boom／downturn |  |  | pass／conditional／fail／insufficient | deteriorating／mixed／bottoming／recovering／insufficient | 单独记录 |

随后逐公司列出`PR 0.55／0.50／0.40／0.30`（港股／H股用校准后`0.44／0.40／0.32／0.24`）对应的中性目标PB、悲观目标PB和价格。目标PB必须由各自归一ROE逐式计算；`1PB／0.5PB`只能标为速查对照。

### 行业同业强弱与领先信号固定格式

| 证券 | 基本面角色／依据 | 20日／60日价格阶段 | 先跌／先稳顺序 | 止跌证据 | 当前作用 |
|---|---|---:|---|---|---|
| 目标股 | 龙头／结构性强势／中性／弱势；基本面依据 |  |  |  | 观察／龙头晚跌首仓候选／继续等待 |
| 弱势同业A | 结构性弱势；基本面依据 |  |  |  | 转熊领先／止跌领先／未确认 |
| 弱势同业B | 结构性弱势；基本面依据 |  |  |  | 转熊领先／止跌领先／未确认 |

表后用一句话给出`bear_leading／unconfirmed／bottoming_candidate／recovery_confirmed／insufficient`、信号日期和置信度。弱势同业至少两只；不足时不输出伪精确状态。弱势股先止跌而基本面龙头仍在下跌时，可标记龙头短期低点候选；不得因此抬高目标价或在估值区外建仓。

### 仓位形成桥固定格式

| 公司 | 当前PR候选档 | 估值支持累计仓位 | 同业择时约束 | 本次新增仓位 | 压力／组合上限 | 最终采用 | 主要瓶颈 |
|---|---|---:|---|---:|---:|---:|---|
|  |  |  |  |  |  |  |  |

从零持仓且当前价已进入主要加仓或更深档时，必须同时说明为什么本次没有一次买到估值支持的累计仓位；“分批”本身不是充分理由，应指出等待的财报确认、压力预算、质量置信度或组合约束。

已持有且触发估值退出时，仓位桥改为：

| 公司 | 当前仓位 | 退出阶段／当前PR | 本档目标剩余仓位 | 已累计减仓 | 本档待减 | 执行约束／最迟日 |
|---|---:|---|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### 每家公司独立阶梯表固定格式

| 档位 | 价格下限 | 价格上限 | 对应市赚率 | 到上限需跌 | 到下限需跌 | 本档新增仓位 | 完成后累计仓位 | 价格＋基本面解锁条件 | 当前状态 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 首仓 |  |  |  |  |  |  |  |  | 已进入／等待／暂停／禁止 |
| 主要加仓 |  |  |  |  |  |  |  |  |  |
| 深度价值 |  |  |  |  |  |  |  |  |  |
| 极端错价 |  |  |  |  |  |  |  |  |  |

跌幅统一以同一估值日当前价计算：

```text
到价格上限需跌 = 1 - 价格上限 / 当前价
到价格下限需跌 = 1 - 价格下限 / 当前价
```

- 当前价已经位于区间内：`到上限需跌`显示`0%（已进入）`，`到下限需跌`继续显示剩余跌幅。
- 当前价低于整个区间：写`已低于区间`，不展示容易误读的负跌幅。
- 价格区间必须按“下限≤上限”排列；到下限的跌幅通常大于到上限的跌幅。
- `本档新增仓位`与`完成后累计仓位`必须同时显示，不得只给累计仓位。
- `对应市赚率`显示区间并注明TTM／预测年度、PE／PB路径和是否为情景辅助；同一表内不得混用口径。
- 周期股每档在`价格＋基本面解锁条件`中同时给出中性／悲观目标PB和`cycle_fundamental_signal`要求；同业股价止跌只能改变时点，不能替代产业信号或净资产质量闸门。

已持有且触发估值退出时，不输出上述建仓表，改为：

| 阶段 | 触发PR | 对应价格 | 累计减仓目标 | 已执行 | 本档待执行 | 状态／条件 |
|---|---:|---:|---:|---:|---:|---|
| 提前兑现 | `S` |  | 10%–15% |  |  | 公司历史与基本面复核后执行 |
| 历史高点区 | `H` |  | 30%–40% |  |  | 最新同口径盈利复核后执行 |
| 确认加速线 | `M`，仅`H<E` |  | 50%–70% |  |  | 历史与基本面共同确认 |
| 市场风险线复核 | `E` |  | 不单独规定 |  |  | 不得只凭PR清仓 |
| 确认硬退出 | 基本面破坏，或风险线、公司历史与最新盈利共同确认明显高估 |  | 80%–100% |  |  |  |
| 确认高估后继续上涨 | 逐档 |  | 每次减剩余仓位25%–50% |  |  | 每次刷新同口径估值 |

表前必须先给出历史有效峰值轮数、峰值平均PR、峰值中位PR、低于市场风险线的峰值比例、市场PR系数、风险复核线`E`、个股锚 `H`、提前线 `S`和样本置信度。

流水线中止时，核心表明确写“当前仓位0%”和“条件价格、尚不可执行”；省略完整预测表、评分拆解、公式、五档风险敏感性和YAML。

### 具体复核日历固定格式

| 公司／目标仓位 | 触发类型 | 具体复核时间／时区 | 日期状态 | 复核事件 | 必查指标 | 通过后的动作 |
|---|---|---|---|---|---|---|
|  | 当前／日历／官方披露／价格 | YYYY-MM-DD HH:MM／时区 | 官方确认／监管最迟／预计窗口／内部检查点／事件驱动 |  |  |  |

官方尚未公布财报日时，必须同时给出“检查官方日历的内部日期”和“不能晚于的监管／计划复核日”，不得制造一个看似精确的公司披露日。官方确认后自动替换为财报前第5个交易日预检、发布后2小时内或下一常规交易时段开盘前快审、完整报表可得后的首个用户时区工作日复核；明显跳空时再列首个完整常规交易日收盘后的价格复核。

另列：当前信息风险首仓、各市赚率边界对应价格、较估值基准价默认8%的过期重算阈值、哪些仓位必须等完整报表才可解锁，以及“财报后新PR仍在档内才加仓、超出档位不追价”的动作规则。价格触发只启动重算，不代替基本面验证。

## 可选：详细模式

只当用户明确要求“展开”、“完整报告”、“详细过程”或“YAML”时，才使用以下完整结构。

## 1. 一句话最终结论

第一句话必须包含：证据截止日、是否通过完整流水线、当前动作、估值位置、首仓区间与比例、条件累计仓位，以及最主要限制。不得以公司介绍、方法或免责声明开场。

## 2. 最终结果总表

| 项目 | 最终结果 |
|---|---|
| 流水线结论 | 全部通过／停止阶段 |
| 当前动作 | 建仓／等待／不合格／退出评估 |
| 当前价格与日期 |  |
| 企业质量 | 背景skill原始分数、评分日期、等级、置信度 |
| 业绩基准情景 | 收入／净利润／EPS；归一化ROE／ROA及历史＋熊市预测权重 |
| 当前估值位置 | 同口径PE_TTM／ROE_TTM／PR_TTM；公司历史分位；基准市赚率及预测年度；修正值如适用 |
| 首仓区间、较现价跌幅与仓位 |  |
| 主要加仓区间、较现价跌幅与累计仓位 |  |
| 深度价值区、较现价跌幅与累计仓位 |  |
| 风险验证后的上限 |  |
| 单股／数量约束 | ≤35%；常态5–8只，按合格低估机会数动态调整 |
| 最大风险与复查触发器 |  |

仅看此表也必须能得到主要决策信息。

## 3. 建仓与加仓阶梯

每家公司使用独立表格，不得合并多只证券：

| 档位 | 价格下限 | 价格上限 | 对应市赚率 | 到上限需跌 | 到下限需跌 | 本档新增仓位 | 完成后累计仓位 | 价格＋基本面条件 | 当前执行 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 首仓 |  |  |  |  |  |  |  |  | 是／否 |
| 主要加仓 |  |  |  |  |  |  |  |  | 是／否 |
| 深度价值 |  |  |  |  |  |  |  |  | 是／否 |
| 极端错价集中 |  |  |  |  |  |  |  |  | 是／否 |

流水线未通过时，表格仍可展示条件预案，但所有“当前执行”为否，当前建议仓位必须为0%。

## 4. 通关与风险总览

| 阶段 | 状态 | 关键结果 | 未通过原因／下一步 |
|---|---|---|---|
| 企业背景调查 | pass／conditional／fail／insufficient |  |  |
| 业绩预测 | usable／conditional／unusable／未运行 |  |  |
| 企业估值 | valid／conditional／invalid／未运行 |  |  |
| 退出监控 | intact／weakened／broken／未运行 |  |  |
| 仓位控制 | executable／conditional／stopped |  |  |

随后列出不超过五项最重要风险和下一次复核触发器。

## 5. 过程与证据

完成结果区后，依次简要展开：

1. 背景调查和质量评分；
2. 熊／基准／牛业绩预测及驱动；
3. 估值输入、公式和价格映射；
4. 核心投资断言和退出触发器；
5. 减弱／破坏压力情景；
6. 仓位公式、五档风险预算敏感性和组合限制；
7. 事实、假设、证据缺口和来源。

避免重复相同数据；关键事实就近附来源。

## 6. 机器可读总结果（仅详细模式且用户需要时）

```yaml
value_investment_pipeline:
  schema_version: "1.7"
  evidence_cutoff: YYYY-MM-DD
  run:
    mode: quick_refresh | earnings_update | full_rebuild
    cache_status: hit | partial | miss | invalid
    cache_path:
    reused_components: []
    refreshed_components: []
    official_change_check_at:
    fundamental_evidence_cutoff:
    latest_price_date:
  company:
  security:
  currency:
  pipeline_status: pass | stopped
  stopped_at:
  current_action: enter | wait | reject | exit_review
  current_price:
  current_price_date:
  research:
    status: pass | conditional | fail | insufficient
    score:
    score_source:
    score_evidence_cutoff:
    confidence:
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
  forecast:
    status: usable | conditional | unusable | not_run
    bear_eps:
    base_eps:
    bull_eps:
  valuation:
    status: valid | conditional | invalid | not_run
    valuation_model_version: ttm-pr-dupont-v4
    position:
    ttm_snapshot:
      period_end:
      accounting_basis: gaap | statutory | adjusted
      pe_ttm:
      roe_ttm_percent:
      roe_average_equity_method: five_quarter_time_weighted | two_point_average | event_date_time_weighted
      pr_ttm:
      single_quarter_annualized: false
      comparability_status: aligned | conditional | invalid
    current_ttm_pr:
    current_ttm_pr_path: pe | pb | both | not_applicable
    base_scenario_pr:
    base_scenario_year:
    adjusted_pr:
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
      roa_ttm_percent:
      three_year_equal_weight_roa_percent:
      roa_primary_profitability_quality_check: true | false
      pr_roe_role: primary_path | scenario_auxiliary | diagnostic_only
      normalized_leverage_roe_percent:
    company_history:
      company_pr_ttm_history_years:
      company_pr_ttm_p25:
      company_pr_ttm_median:
      company_pr_ttm_p75:
      current_pr_ttm_percentile:
      historical_comparability_breaks: []
    roa_adjustment:
      status: corrected | not_required | insufficient
      original_roa_percent:
      corrected_roa_percent:
      profit_numerator:
      asset_denominator_method:
      formula:
      reason:
      decision_use: quality_and_leverage_check_only
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
    pr_usage_note:
    historical_selection_rule:
    historical_selected_years: []
    stable_three_year:
      roe_values: []
      equal_weight_roe_percent:
      roe_standard_deviation_points:
      roe_cv_percent:
      quantitative_status: strict_stable | relaxed_eligible | unstable | not_applicable
      qualitative_comparability: confirmed | not_confirmed | unknown | not_applicable
      tier: strict_stable | relaxed_stable | unstable | not_applicable
      policy: strict | controlled_relaxation
      strict_candidate_count:
      minimum_candidate_count:
      candidate_scarcity_confirmed: true | false
      relaxed_position_cap_percent: 15
      strict_reconfirmation_reports_required: 2
      neutral_anchor_usable: true | false
    cyclical_assessment:
      applicability: cyclical | not_cyclical | uncertain
      cycle_driver:
      company_role: leader | mainstream | high_cost_tail | uncertain | not_applicable
      cycle_phase_status: complete_phase_balanced | provisional_equal_weight | not_applicable
      cycle_phase_labels: []
      historical_cycle_phase_balanced_roe_percent:
      historical_cycle_phase_balanced_roa_percent:
      asset_quality_status: pass | conditional | fail | insufficient | not_applicable
      cycle_fundamental_signal: deteriorating | mixed | bottoming | recovering | insufficient | not_applicable
      cycle_signal_evidence_cutoff:
      equity_timing_is_separate: true
      pb_bands:
        neutral_pr_0_55:
        bear_pr_0_55:
        neutral_pr_0_50:
        bear_pr_0_50:
        neutral_pr_0_40:
        bear_pr_0_40:
        neutral_pr_0_30:
        bear_pr_0_30:
    current_weak_roe_percent:
    historical_conservative_roe_anchor_percent:
    current_weak_roa_percent:
    historical_conservative_roa_anchor_percent:
    initial_entry_price_low:
    initial_entry_price_high:
    initial_entry_pr_low:
    initial_entry_pr_high:
    initial_entry_pr_basis:
    initial_entry_decline_low_percent:
    initial_entry_decline_high_percent:
    add_price_low:
    add_price_high:
    add_pr_low:
    add_pr_high:
    add_pr_basis:
    add_decline_low_percent:
    add_decline_high_percent:
    deep_value_price_low:
    deep_value_price_high:
    deep_value_pr_low:
    deep_value_pr_high:
    deep_value_pr_basis:
    deep_value_decline_low_percent:
    deep_value_decline_high_percent:
  exit_monitoring:
    fundamental_status: intact | weakened | broken | insufficient | not_run
    add_permission: allowed | paused | prohibited | unknown
    weakened_loss_high_percent:
    broken_loss_high_percent:
  industry_relative_timing:
    status: bear_leading | unconfirmed | bottoming_candidate | recovery_confirmed | insufficient
    signal_date:
    confidence:
    industry_benchmark:
    target_role: strong | neutral | weak
    peer_universe: []
    weak_peer_group: []
    weak_peers_stopped_new_lows_count:
    sector_breadth_improving: true | false | unknown
    target_in_valid_valuation_band: true | false
    timing_effect: wait | use_lower_initial_tranche | allow_normal_initial_tranche | no_change
    evidence_gaps: []
  position:
    executable: true | false
    current_pr:
    current_pr_basis:
    current_pr_valuation_tier:
    valuation_supported_cumulative_percent_low:
    valuation_supported_cumulative_percent_high:
    current_add_percent_low:
    current_add_percent_high:
    stress_cap_percent:
    portfolio_cap_percent:
    final_adopted_percent_low:
    final_adopted_percent_high:
    binding_constraint:
    initial_percent_low:
    initial_percent_high:
    add_tranche_percent_low:
    add_tranche_percent_high:
    add_cumulative_percent_low:
    add_cumulative_percent_high:
    deep_value_tranche_percent_low:
    deep_value_tranche_percent_high:
    deep_value_cumulative_percent_low:
    deep_value_cumulative_percent_high:
    extreme_mispricing_price_low:
    extreme_mispricing_price_high:
    extreme_mispricing_pr_low:
    extreme_mispricing_pr_high:
    extreme_mispricing_pr_basis:
    extreme_mispricing_tranche_percent_low:
    extreme_mispricing_tranche_percent_high:
    extreme_mispricing_cumulative_percent_low:
    extreme_mispricing_cumulative_percent_high:
    risk_validated_cap_percent:
    maximum_single_stock_percent: 30
    preferred_stock_count_low: 6
    preferred_stock_count_target: 8
    preferred_stock_count_high: 10
    stock_count_policy: opportunity_driven
    listing_market:
    market_preference_factor:
    current_information_risk_tranche:
      eligible: true | false
      percent_low:
      percent_high:
      rationale:
      blocking_risks: []
    unlocked_only_after_full_review_percent:
  remediation_requirements: []
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

未知字段留空，不得用未经确认的值填充。
