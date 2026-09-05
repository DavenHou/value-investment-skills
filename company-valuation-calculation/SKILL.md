---
name: company-valuation-calculation
description: 对A股、港股或美股按企业类型计算条件估值区间，以同口径PE_TTM／ROE_TTM市赚率或周期PB路径为主，结合三年盈利情景、公司自身历史与杜邦ROE拆解判断输入可靠性。用于计算合理估值、判断当前估值位置或把盈利预测转换为价格带；不把任何单一指标当作买卖答案。
---

# 企业估值计算

把市赚率作为一种**条件相对估值工具**，而不是企业质量证明、确定的内在价值或机械买卖信号。稳定企业的当前主快照使用同口径`PE_TTM / ROE_TTM`；周期股仍走PB与完整周期归一化ROE路径。所有对象都必须拆解ROE来源，并用公司自身历史、三年情景与压力测试约束结论。

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

1. **ROE稳定的非周期股**：以最近三个可比完整年度ROE等权平均与未来三个完整财年预测组成中性归一ROE；当前快照使用同一口径的`PE_TTM / ROE_TTM`。三年稳定性默认作为严格优先筛选条件，但在严格合格候选数低于组合最低需求时可启用受控放宽；必须标成`relaxed_stable`，不得与`strict_stable`混同。
2. **周期股或困境反转股**：以当前PB和覆盖完整周期的归一化ROE为主；原始TTM PE通常失真。
3. **成长股或科技股**：市赚率只能作为情景辅助。未来ROE、回购和再投资价值未可靠建模时，直接判定“不足以估值”。
4. **金融企业**：可展示PE/PB/ROE结果，但必须另查资产质量、资本充足率、准备金和信用周期，不能只凭市赚率下结论。
5. **指数**：先区分红利／质量指数和宽基指数；指数阈值只是经验校准，不等于单一公司的合理价值。

## 执行计算

计算前必须阅读 [methodology.md](references/methodology.md)和[杜邦拆解与ROE可靠性](references/dupont-and-roe-reliability.md)，严格采用其中的TTM对齐、ROE单位、基础公式、归一化盈利能力权重、杜邦拆解、目标价格换算和分支规则。需要重复计算或交叉核对时使用：

```bash
python scripts/calculate_valuation.py --pe-ttm 12.5 --roe-ttm-percent 25 --payout-percent 40 --current-price 100
python scripts/calculate_normalized_profitability.py --company-type stable --historical-roe 18,20,22 --forecast-base-roe 20,21,22 --forecast-bear-roe 17,18,19 --historical-roa 9,10,11 --forecast-base-roa 10,10.5,11 --forecast-bear-roa 8,9,9.5 --current-ttm-roe 21 --current-ttm-roa 10.5 --stable-years-comparable confirmed
python scripts/calculate_normalized_profitability.py --company-type stable --historical-roe 11,20,29 --forecast-base-roe 20,21,22 --forecast-bear-roe 15,17,18 --historical-roa 8,10,12 --forecast-base-roa 10,10.5,11 --forecast-bear-roa 7.5,8.5,9 --current-ttm-roe 22 --current-ttm-roa 11 --stable-years-comparable confirmed --stability-policy controlled_relaxation --strict-candidate-count 4 --minimum-candidate-count 6
python scripts/calculate_normalized_profitability.py --company-type cyclical --historical-roe 5,8,12,20,18,11,7,4,9,15 --historical-phases trough,trough,recovery,boom,boom,downturn,downturn,trough,recovery,boom --forecast-base-roe 10,12,14 --forecast-bear-roe 6,7,8
```

估值用于建仓决策时，还必须读取 [scenario-weighting.md](references/scenario-weighting.md)：先并列中性与悲观结果，再按企业类型、两情景差距和有证据的行业宏观状态形成透明的决策权重。不得默认永远使用中性或悲观单一口径，也不得用加权平均覆盖已确认的基本面或行业硬风险。

核心要求：

- `PE_TTM`、`ROE_TTM`和每股价格必须来自相同股份类别、同一截止日及相同会计口径；有完整TTM时禁止用单季乘四年化替代。
- ROE以“百分数点”输入脚本，例如31%输入`31`，不是`0.31`。
- 同时存在PE、PB和ROE时，分别计算并解释差异；不得静默取平均。
- 负PE、零或负ROE、重大一次性收益、股本或会计口径突变时，停止机械计算并先重建可比口径。
- TTM ROE优先用最近四季可比归母净利润除以五个连续季末归母净资产的季度时间加权均值；只能取得期初期末时可用两点平均并降低口径质量。不得简单相加季度ROE，也不得把单季ROE乘四。
- 市赚率公式仍以ROE为输入；ROA不直接代入PE／PB市赚率公式。若ROE超过40%或被回购、净资产收缩、杠杆显著抬高，当前ROE市赚率降为诊断项，盈利质量改由ROA／ROIC、自由现金流和正常资本结构下的重算ROE判断。
- 归一化前先逐年用可比的经常性归母净利润计算ROE和ROA；默认并列计算中性与悲观两套口径。稳定非周期对象的中性历史锚使用最近三个可比完整年度ROE等权平均，并报告`strict_stable／relaxed_stable／unstable`；科技对象保留近五年近期加权；周期股的中性历史锚必须使用覆盖低谷—复苏—景气—回落的阶段平衡ROE。悲观口径使用历史弱年份锚与未来三年熊市场景。ROA严格跟随ROE的年份、期间、阶段和情景。不得跨越增发、回购、并购或资产剥离直接平均净利润金额。
- 不机械采用历史最低单年。先剔除纯会计性且不可重复的一次性异常，但真实经济亏损、持续性减值和可复现的周期低谷必须保留；历史普通加权值只作对照，不作为默认估值输入。
- 中性归一ROE用于正常经营假设下的筛选、估值排序和首仓价格参考；悲观归一ROE用于压力测试、深档加仓许可和仓位上限。不得只用悲观口径淘汰公司，也不得只用中性口径放大仓位。
- 对非金融企业至少做三因素杜邦；若ROE上升主要由权益乘数、净资产收缩或债务推动，必须重算正常杠杆下的ROE并设置杠杆复核闸门。
- 任一当前TTM或最近三年ROE超过40%时强制设置`extreme_roe_review_required`，核查回购导致的权益缩减、负或过小净资产、举债回购、股份数变化、权益乘数与利息覆盖，并强制显示同口径ROA、ROIC与每股FCF。未完成前不得用该ROE生成可执行PR价格带；确认为回购／杠杆失真后，PR永久降为诊断项，直至用正常资本结构重算ROE。

## 判断而非套答案

`0.4／0.5／0.6`的低估区、`1.0`的名义合理值、红利指数`1.0`和宽基指数`1.5`等都来自原始资料中的经验标尺。必须标记为“框架经验阈值”，并用企业自身同口径滚动`PR_TTM`分布、同行、盈利质量、资本配置和三年情景校准。企业长期高于或低于1时先解释结构原因，不机械判定永远不能买或必须买。

周期股便宜还不够。先以盈利对产品价格、订单、库存、资本开支和产能利用率的敏感性确认其周期属性，再核验公司是龙头、主流还是高成本尾部企业，并检查净资产中的库存、固定资产、商誉、减值和有息负债是否真实可穿越低谷。周期ROE无法覆盖完整周期或无法按阶段归类时，只能给区间／条件结果，不输出伪精确单点。

周期股必须把产业基本面右侧信号与股票价格择时分开：`cycle_fundamental_signal`检查现货／期货价格、订单、库存、产能出清、开工率、资本开支和已落地的供给侧／“反内卷”政策；同业股价止跌属于下游择时信号，不能冒充产业反转。两者只调整情景权重、首仓时点和分批节奏，不改变公式、质量分或基础目标PR。

对周期股的每个目标PR必须按`目标PB = 目标PR × 归一化ROE² / 100`计算公司专属PB线，并映射到价格。资料中的“15% ROE龙头约1PB、10% ROE主流企业约0.5PB”只是`PR≈0.5`下的速查例子，不得作为跨公司硬筛选线。

股东回报修正必须按市场调整：A股以可持续分红和注销式回购为主；美股看股息加净回购，并扣除股权激励与增发稀释，不因股息率低机械加罚；港股同时看投资者实际税后股息、净回购、流动性与汇率。跨市场时必须读取 [references/cross-market-calibration.md](references/cross-market-calibration.md)。

港股／H股执行用户确认的固定市场校准：所有用于建仓和估值退出复核的目标PR阈值按基础阈值乘以`0.80`，观察到的公司PR本身不乘系数。因而基础`PR=1.00`风险复核线对应港股`PR=0.80`；基础首仓／主要加仓／深度价值／极端错价阈值`0.55／0.50／0.40／0.30`对应港股`0.44／0.40／0.32／0.24`。退出复核线须结合公司历史、最新同口径盈利与基本面状态复核后才产生减仓动作。该固定折价已吸收一般性的港股税后回报、流动性、汇率和投资者结构差异，不得再以同一组理由重复下调目标价或仓位；只有可验证的证券特有额外风险才能另加安全边际，并须单列证据。

## 交付结果

严格按 [output-schema.md](references/output-schema.md) 的顺序输出。**先完成结论交付，再解释计算过程**：首屏必须直接给出当前估值位置、核心条件价格区间、最重要的判断与置信度；随后展示情景敏感性。只有这些结论已经完整呈现后，才能进入数据口径、公式代入、交叉检查和风险细节。不得以资料搜集过程、公司背景、公式或长篇风险提示开场，也不得要求读者看完计算过程才能找到结论。

必要时读取 [source-calibration-notes.md](references/source-calibration-notes.md) 解释公式来源与仍待验证的经验规则。

不要把“低市赚率”写成买入建议，也不要把历史案例拟合写成已证明的因果规律。资料不足时，交付缺口清单和可计算部分。
