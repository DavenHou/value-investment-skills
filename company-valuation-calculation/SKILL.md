---
name: company-valuation-calculation
description: 对A股、港股或美股按企业类型计算条件估值区间，以同口径PE_TTM／ROE_TTM市赚率或周期PB路径为主，结合三年盈利情景、公司自身历史与杜邦ROE拆解判断输入可靠性。用于计算合理估值、判断当前估值位置或把盈利预测转换为价格带；不把任何单一指标当作买卖答案。
---

# 企业估值计算

把市赚率作为一种**条件相对估值工具**，而不是企业质量证明、确定的内在价值或机械买卖信号。稳定企业的当前主快照使用同口径`PE_TTM / ROE_TTM`；周期股走PB路径，ROE 取值保守优先。所有对象都必须拆解ROE来源，并用公司自身历史、三年情景与压力测试约束结论。

## 证据完整性硬闸门

- PE、PB、EPS、净资产、ROE／ROA、股份数、汇率和价格必须可追溯到正式上游交接、可靠行情或列明输入的确定性计算；不得为得到目标价而补造任何输入。
- 缺少必要输入时只输出可验证部分并把估值标为`conditional／invalid／non_actionable`，不得用行业平均、搜索摘要或主观中点冒充公司正式值。
- 固定公式、情景权重和阈值不得临时改写。任何新插值档、修正系数或替代口径只能作为明确标注的非执行敏感性，未经用户批准不能写回正式价格带。

## 先组合其他研究技能

估值前先获得业务与数据基础：

- 用 `company-background-research` 核验商业模式、管理层、治理、盈利真实性和企业质量。质量或会计口径未过关时，不因估值低而给出积极结论。
- 需要未来盈利、利润率、ROE或ROA时，用 `company-earnings-forecast` 建立未来三个完整财年的熊市／基准／牛市情景；归一化盈利能力同时读取基准与熊市场景的逐年净利润、平均归母净资产、平均总资产、ROE和ROA，不得直接外推单年高点。
- 对上市非金融企业，用 `pure-cash-coverage` 补充确定现金下限和严格净金融资产覆盖率；该结果是资产安全垫，不并入市赚率公式。

当估值用于建仓方案而不是单纯的独立计算时，执行上游闸门：`company-background-research.research_status`必须为`pass`，`company-earnings-forecast.forecast_status`必须为`usable`。任一未通过时可以展示历史口径或教育性的估值敏感性，但 `valuation_handoff.valuation_status` 必须标为`non_actionable`，不得交给仓位skill生成可执行方案。

## 界定计算对象

先确认公司、证券代码、上市地、币种、A/H/ADS等股份类别、估值日、最新报告期、TTM或年度口径。跨市场或双重上市时分别计算价格、税负、汇率与每股数据，不能混用。

将对象分到最接近的一类：

1. **ROE稳定的非周期股**：乐观、中性与悲观归一ROE共用“弱年份锚与当前弱运行率取低”形成的历史悲观锚50%，再分别接入乐观、基准或熊市F1–F3预测50%；当前快照使用同一口径的`PE_TTM / ROE_TTM`。最近三年等权ROE均值仅作稳定性与历史对照。
2. **周期股或困境反转股**：以当前PB和覆盖完整周期的归一化ROE为主；原始TTM PE通常失真。
3. **成长股或科技股**：市赚率只能作为情景辅助。未来ROE、回购和再投资价值未可靠建模时，直接判定“不足以估值”。
4. **金融企业**：可展示PE/PB/ROE结果，但必须另查资产质量、资本充足率、准备金和信用周期，不能只凭市赚率下结论。
5. **指数**：先区分红利／质量指数和宽基指数；指数阈值只是经验校准，不等于单一公司的合理价值。

## 执行计算

计算前必须阅读 [methodology.md](references/methodology.md)和[杜邦拆解与ROE可靠性](references/dupont-and-roe-reliability.md)，严格采用其中的TTM对齐、ROE单位、基础公式、归一化盈利能力权重、杜邦拆解、目标价格换算和分支规则。需要重复计算或交叉核对时使用：

```bash
python scripts/calculate_valuation.py --pe-ttm 12.5 --roe-ttm-percent 25 --payout-percent 40 --current-price 100
python scripts/calculate_normalized_profitability.py --company-type stable --historical-roe 18,20,22 --forecast-base-roe 20,21,22 --forecast-bull-roe 23,24,25 --forecast-bear-roe 17,18,19 --historical-roa 9,10,11 --forecast-base-roa 10,10.5,11 --forecast-bull-roa 11.5,12,12.5 --forecast-bear-roa 8,9,9.5 --current-ttm-roe 21 --current-ttm-roa 10.5 --stable-years-comparable confirmed
python scripts/calculate_normalized_profitability.py --company-type stable --historical-roe 11,20,29 --forecast-base-roe 20,21,22 --forecast-bear-roe 15,17,18 --historical-roa 8,10,12 --forecast-base-roa 10,10.5,11 --forecast-bear-roa 7.5,8.5,9 --current-ttm-roe 22 --current-ttm-roa 11 --stable-years-comparable confirmed --stability-policy controlled_relaxation --strict-candidate-count 4 --minimum-candidate-count 6
python scripts/calculate_normalized_profitability.py --company-type cyclical --historical-roe 5,8,12,20,18,11,7,4,9,15 --historical-phases trough,trough,recovery,boom,boom,downturn,downturn,trough,recovery,boom --forecast-base-roe 10,12,14 --forecast-bear-roe 6,7,8
```

估值用于建仓决策时，还必须读取 [scenario-weighting.md](references/scenario-weighting.md)。该页定义唯一动作线`决策PR`及其适用范围：

全部企业类型共用一条动作线，但公式按企业类型二选一（`single-decision-pr-v2`）：

```text
周期股／困境反转：决策PR = 100 × 同期PB ÷ (执行ROE百分数点)²
非周期股：        决策PR = PE_TTM ÷ 执行ROE
```

`执行ROE`与历史窗口按[scenario-weighting.md](references/scenario-weighting.md)取值；正式所选档归一ROE由[methodology.md](references/methodology.md)生成。历史峰值只能使用峰值日当时可得的同口径输入。

**8PB 硬约束**：当前PB > 8 时一律不建仓；它不进入高估线。实际高估线 `E = min(E_market, 个股历史峰值PR)`。

非周期类型的历史、当前 TTM 与正式所选档归一ROE按[scenario-weighting.md](references/scenario-weighting.md)保守取低；差距超过该页复核线时说明原因，不把复核线当成取低的启动条件。周期股分歧由`cycle_anchor_conflict`处理。


任何企业类型在任一时点都只有一个`决策PR`。`核验PR＝PE_TTM ÷ ROE_TTM`只用于财报估值核验和杜邦检查，不产生动作许可；不得并列第二个用于退出比较的动作PR。两者相差百分之几属预期内（平均权益对期末权益），并列展示即可。

核心要求：

- `PE_TTM`、`ROE_TTM`和每股价格必须来自相同股份类别、同一截止日及相同会计口径；有完整TTM时禁止用单季乘四年化替代。
- ROE以“百分数点”输入脚本，例如31%输入`31`，不是`0.31`。
- 同时存在PE、PB和ROE时，分别计算并解释差异；不得静默取平均。
- 负PE、零或负ROE、重大一次性收益、股本或会计口径突变时，停止机械计算并先重建可比口径。
- TTM ROE **默认把最近四个单季度的净资产收益率直接相加**（原始资料的方法，A股用同花顺 F10→财务→单季度→净资产收益率）。只有单季ROE不可得或存在重大股本变动使相加失真时，才改用五个连续季末权益的时间加权均值，并标注替代口径与两者差异。任何情况下都不得把单季ROE乘四。
- 市赚率公式仍以ROE为输入；ROA不直接代入PE／PB市赚率公式。若ROE超过40%或被回购、净资产收缩、杠杆显著抬高，当前ROE市赚率降为诊断项，盈利质量改由ROA／ROIC、自由现金流和正常资本结构下的重算ROE判断。
- 归一化前先逐年用可比的经常性归母净利润计算ROE和ROA；默认并列计算乐观、中性与悲观三套口径。稳定非周期对象的三套正式口径共用历史悲观锚50%，对应情景F1/F2/F3分别占20%/20%/10%；最近三年等权ROE均值仅用于`strict_stable／relaxed_stable／unstable`分级和对照。科技对象保留近五年近期加权；周期股的中性历史锚必须使用覆盖低谷—复苏—景气—回落的阶段平衡ROE。ROA严格跟随ROE的锚来源、年份、期间、阶段和情景。不得跨越增发、回购、并购或资产剥离直接平均净利润金额。
- 周期股取最近五年最低单年前先剔除纯会计性且不可重复的一次性异常，但真实经济亏损、持续性减值和可复现的周期低谷必须保留；最低ROE不为正时不输出可执行第二公式。
- 周期股按[methodology.md](references/methodology.md)的股息率选档与重大业绩下滑保护选择正式归一ROE进入唯一动作线；悲观归一ROE仍用于压力测试、深档加仓许可和仓位上限。其他类型仍按各自分支执行。
- 对非金融企业至少做三因素杜邦；若ROE上升主要由权益乘数、净资产收缩或债务推动，必须重算正常杠杆下的ROE并设置杠杆复核闸门。
- 任一当前TTM或最近三年ROE超过40%时强制设置`extreme_roe_review_required`，核查回购导致的权益缩减、负或过小净资产、举债回购、股份数变化、权益乘数与利息覆盖，并强制显示同口径ROA、ROIC与每股FCF。未完成前不得用该ROE生成可执行PR价格带；确认为回购／杠杆失真后，PR永久降为诊断项，直至用正常资本结构重算ROE。
- **净资产收缩时必须实际算出"正常资本结构下的重算ROE"并加进取低集合，不得因为 ROIC 高于 ROE 不绑定就放行**（第 25 条）。回购同时缩小 ROE 与 ROIC 的分母，ROIC 闸门对回购型失真是盲的。`重算ROE = TTM归母净利 ÷ (同日期末归母权益 + 与执行ROE 同窗口的累计回购)`；重算后复核 `PR=1` 隐含PB `= 重算ROE²/100` 是否回到 8 以内。
- 上述重算必须调用`scripts/calculate_valuation.py`中的截止日校验；仓位和流水线skill只消费其计算护照与最终`decision_pr`，不得复制公式或自行重算。

## 判断而非套答案

`0.4／0.5／0.6`的低估区、`1.0`的名义合理值、红利指数`1.0`和宽基指数`1.5`等都来自原始资料中的经验标尺。必须标记为“框架经验阈值”，并用企业自身同口径滚动`PR_TTM`分布、同行、盈利质量、资本配置和三年情景校准。企业长期高于或低于1时先解释结构原因，不机械判定永远不能买或必须买。

周期股便宜还不够。先以盈利对产品价格、订单、库存、资本开支和产能利用率的敏感性确认其周期属性，再核验公司是龙头、主流还是高成本尾部企业，并检查净资产中的库存、固定资产、商誉、减值和有息负债是否真实可穿越低谷。周期ROE无法覆盖完整周期或无法按阶段归类时，只能给区间／条件结果，不输出伪精确单点。


周期股还必须用同日PB并列计算当前弱运行PR、决策PR和悲观PR，输出`aligned／material_gap／regime_split／insufficient`的盈利锚分歧状态。`material_gap`最多允许4%信息风险首仓且锁定后续档；`regime_split`暂停新增并对已有持仓启动退出复核。**`regime_split` 的默认动作是减仓一半**——两种ROE假设给出割裂结论时，按原始资料中远海控案例的纪律执行（“即便有可能卖飞，也要遵守纪律”），不因可能卖飞而推迟。该闸门不得反过来修改决策PR或目标PB造成重复惩罚。

周期股按`目标PB = 目标PR × 执行ROE² / 100`映射价格；非周期股按`目标PE = 目标PR × 执行ROE`映射价格。两者都只用唯一决策PR及其执行ROE，不做情景加权合成价格。

历史`S／H／M／E`必须在每个峰值日复用同类型公式：周期股用PB形，非周期股用`PE_TTM ÷ 执行ROE`。无法用当时可得数据复算的轮次进入剔除清单，不得用事后数据回填。

股东回报修正必须按市场调整：A股以可持续分红和注销式回购为主；美股看股息加净回购，并扣除股权激励与增发稀释，不因股息率低机械加罚；港股同时看投资者实际税后股息、净回购、流动性与汇率。跨市场时必须读取 [references/cross-market-calibration.md](references/cross-market-calibration.md)。

跨市场规则用同一个市场系数 `c` 同时作用于买入线与高估线：港股／H股 `c = 0.90 × (1 − 股息率 × t ÷ 10%)`（`t` 为港股通个人股息税，H股与红筹均按 20% 计，28% 作敏感性）；A股／美股 `c = 1.00`；恒生`1.35`、恒生国企`1.20`、A股红利指数`1.00`、宽基指数`1.50`。买入线 `0.50／0.40／0.30 × c` 与原始读数取更严；`E_market = c`。观察到的公司PR 本身永远不乘系数。实际高估线 `E = min(市场高估线, 个股历史峰值PR)`；输出必须同时给出**归一化估值位置 `= 决策PR ÷ E`**，使 1.0 在任何市场都代表高估线，卖出档按归一化 `0.80／0.90／1.00` 取 20%–30%／50%–60%／80%–100%。

最终高估线只在市场线与个股历史峰值之间取小：`E = min(E_market, 个股历史峰值PR)`。8PB 是独立建仓禁令：**当前PB > 8 时一律不建仓**，但不进入`E`。A+H 两地上市以H股为标杆，H股高估后A股一并卖出。退出复核线须结合公司历史、最新同口径盈利与基本面状态复核后才产生减仓动作；市场折价不得以同一组理由重复下调目标价或仓位。

## 交付结果

严格按 [output-schema.md](references/output-schema.md) 的顺序输出。**先完成结论交付，再解释计算过程**：首屏必须直接给出当前估值位置、核心条件价格区间、最重要的判断与置信度；随后展示情景敏感性。只有这些结论已经完整呈现后，才能进入数据口径、公式代入、交叉检查和风险细节。不得以资料搜集过程、公司背景、公式或长篇风险提示开场，也不得要求读者看完计算过程才能找到结论。

必要时读取 [source-calibration-notes.md](references/source-calibration-notes.md) 解释公式来源与仍待验证的经验规则。

不要把“低市赚率”写成买入建议，也不要把历史案例拟合写成已证明的因果规律。资料不足时，交付缺口清单和可计算部分。
