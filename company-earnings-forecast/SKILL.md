---
name: company-earnings-forecast
description: Build source-backed quarterly, annual, or three-year revenue, margin, and earnings forecasts for a public or private company in any industry. Use when asked to forecast company performance, model earnings, estimate revenue or EPS, assess a result before earnings, or construct bull/base/bear operating scenarios from filings, earnings calls, and upstream, downstream, competition, pricing, capacity, capital-investment, and cycle evidence.
---

# Industry-Driven Company Earnings Forecast

Build a conditional operating forecast, not a price target or investment recommendation. Treat each forecast as valid only for its stated cutoff date, reporting period, accounting basis, industry classification, and scenario assumptions.

## Evidence-integrity gate

- Reported figures and management guidance must be traceable to a dated source. Forecast values must be deterministic outputs of disclosed inputs and assumptions; never present a model estimate as a reported fact or formal guidance.
- Missing balance-sheet, share-count, segment, or driver inputs remain empty or make the handoff `conditional／unusable`; do not reverse-engineer a precise value merely to complete EPS, ROE, ROA, or a three-year table.
- When a prior formal forecast conflicts with new evidence, preserve the difference, identify the changed input, invalidate affected downstream fields, and then rebuild. Never silently select the more favorable case.

## Investment-pipeline gate

For the full investment pipeline or position sizing, first read `company-background-research.research_handoff`. Continue to an actionable investment handoff only when `research_status: pass` and `eligible_next_step: earnings_forecast`; otherwise report the remediation requirement. For `quick_valuation`, background research is skipped by scope: a source-backed, internally reconciled three-year forecast may have `forecast_status: usable` and `eligible_next_step: valuation` for valuation only, with `upstream_research_status: skipped_by_scope`. This does not authorize position sizing. A standalone forecast requested only for planning or analysis remains `non_actionable`.

## Set the forecast horizon

When the user asks for the next three years, forecast the current fiscal year plus the next two fiscal years, and label the current year as part actual and part forecast where applicable. Use three full future fiscal years only when the user explicitly requests that convention. State the fiscal-year end and the forecast cutoff.

When the forecast will feed `company-valuation-calculation`'s normalized profitability model, always add three full forecast fiscal years after the latest completed fiscal year (`F1`–`F3`), even if the ordinary response also shows a part-actual current year. The valuation handoff must keep each bear year separate; a single three-year average is insufficient for recency weighting.

Also supply a conservative current run-rate when it can be calculated comparably. Use the lower of the latest completed fiscal-year ROE／ROA and a defensible TTM or current-fiscal-year annualised bear run-rate; do not annualise a seasonal single quarter. This field is an input to the valuation skill's historical conservative anchor, not a replacement for the separate F1–F3 bear case.

Use quarterly precision only for the current and next fiscal year when data supports it. Present years two and three annually unless an observable, contracted, or regulated schedule supports quarterly detail. Read `references/multi-year-forecast.md` whenever the horizon exceeds one fiscal year.

## Choose the model before modelling

Classify each material business segment before choosing its forecast drivers. Read `references/industry-archetypes.md` and select the closest archetype; use more than one when the company has genuinely different businesses. Do not force a manufacturing volume-price model onto a bank, a software business, or a property developer.

Map the relevant causal chain:

```text
upstream inputs and supply → industry price/capacity/inventory → customer or end-market demand → company volume, price, mix, and cost → earnings
```

State the company position in the chain and identify which links are observable. Treat an upstream, customer, or competitor datapoint as evidence only after explaining its transmission path to the company.

## Required inputs

Establish these before modelling. Ask only for information unavailable from supplied material or authoritative sources.

- Company/legal entity, ticker, and reporting currency.
- Forecast period and fiscal-year convention: next quarter, next fiscal year, current fiscal year plus two years, or another stated multi-period range.
- Forecast metrics: revenue, gross margin, operating profit, net profit, EPS, or another named metric.
- Latest reported period and a data cutoff date.

If a key input or reliable source is unavailable, state the gap and make the smallest explicit assumption necessary. Never invent a reported figure, contract, policy, or management guidance.

## Workflow

### 1. Establish the baseline and industry position

Use the latest filings, earnings release, investor presentation, and earnings-call transcript where available. Record historical revenue, margins, operating costs, capacity/utilisation, guidance, and non-recurring items. Keep reported, adjusted, and forecast values separate.

Research current data when needed. Prefer primary sources and attach a link to every material factual claim. Record the relevant end-market, customer, input, competitor, and regulatory exposures. See `references/forecast-framework.md` for the evidence hierarchy and driver checklist.

### 2. Build a revenue driver tree

Break revenue into the most decision-useful dimensions disclosed by the company: product, geography, customer type, business unit, volume, price, and foreign exchange. Use the simplest tree that explains most of the change.

For each material driver, state:

- starting value and source;
- forecast assumption and mechanism;
- leading evidence or counter-evidence;
- effect on revenue and confidence.

Do not extrapolate a consolidated revenue growth rate when disclosed drivers or a material structural change make that misleading. Where physical or operational units exist, forecast them first and reconcile them to revenue. Where they do not, use the archetype-specific unit economics or contractual driver.

For a three-year forecast, build a separate driver path for each year. Explain the expected timing of demand, price, capacity, share, and mix changes rather than applying a single CAGR to every future year.

### 3. Test the cycle, competition, and pricing regime

Determine whether the relevant market is in demand recovery, restocking, tight supply, overcapacity, destocking, or another identifiable regime. Read `references/competition-and-cycles.md` when the industry is cyclical, capacity-intensive, commodity-linked, or exposed to discounting.

Test the five channels that usually change a forecast most:

1. end-market volume or activity;
2. realised price, discounting, and contract resets;
3. supply, capacity additions, inventory, and utilisation;
4. upstream input costs and contractual pass-through;
5. market share, product mix, and technology substitution.

Distinguish a demand shortfall from a price war. If volume is growing while realised price, industry utilisation, or gross margin falls, investigate competitive discounting or adverse mix rather than describing the outcome as simple demand weakness.

### 4. Bridge revenue to earnings

Forecast gross margin and operating costs separately. Test upstream input costs, wages, freight, capacity utilisation, mix, pricing, and fixed-cost leverage. Separate recurring operating performance from FX, financing, tax, fair-value, and one-off items.

Explain operating leverage explicitly: a revenue shortfall can reduce profit by more than the proportional revenue change when fixed costs are high. For financial companies, bridge yield, funding cost, credit losses, fee income, and capital instead of cost of revenue.

For multi-year forecasts, test whether capex, working capital, debt, depreciation, regulatory investment, or research spending changes the earnings path. Do not show an attractive profit path that requires unmodelled capacity or ignores the cash and capital required to produce it.

When feeding valuation, extend each annual scenario through a compact balance-sheet path and calculate rather than guess:

```text
ROE_year = attributable net profit / average attributable equity
ROA_year = attributable net profit / average total assets
```

Use beginning/end averages adjusted for the timing of material issuance, buybacks, dividends, acquisitions or disposals. If assets or equity cannot be forecast credibly, leave ROE/ROA empty and mark the handoff conditional; do not infer them from the income statement alone.

For every valuation-bound F1–F3 handoff, retain the calculation bridge for attributable net profit, beginning／ending attributable equity, beginning／ending total assets, and the resulting average balances. Bear-case ROE and ROA are outputs of that bridge, never direct analyst inputs or placeholders. Do not backsolve profit or balance-sheet values from a desired ROE. If any year cannot be reconciled from disclosed starting balances and explicitly stated operating／capital assumptions, mark that year and the overall handoff `conditional／insufficient`; downstream valuation must not use the unsupported years for normalized profitability, decision PR, or price bands.

### 5. Test the business and industry assumptions

Use the five-force check in `references/forecast-framework.md`:

1. supplier bargaining power and input availability;
2. customer bargaining power and downstream demand;
3. existing rivalry, price pressure, inventory, and capacity additions;
4. new entrants and expansion by competitors;
5. substitutes or technology changes.

Also test management execution, product roadmap, capacity, regulation, and policy exposure. Convert only material findings into named forecast assumptions; keep the rest in the risk register.

### 6. Produce scenarios, not a false point estimate

Create bear, base, and bull cases by changing causal assumptions, not only top-line growth rates. For each case, name the changed volume/activity, price, cost, utilisation, share, or credit assumptions and state the observable trigger. Do not assign probabilities unless a defensible method or user-provided probabilities exist.

Reconcile each scenario to historical ranges, company guidance, and the revenue/margin bridge. Flag a forecast as low confidence when the outcome is driven by unresolved policy, a customer decision, a commodity move, or another unobservable variable.

For a three-year forecast, distinguish a near-term evidence-based case from years-two-and-three normalisation assumptions. Explicitly lower confidence with forecast distance unless a contract, regulation, capacity schedule, or other primary evidence constrains the outcome.

### 7. Perform quality control

Before responding, verify:

- period labels, currency, units, and accounting basis are consistent;
- revenue components sum to total revenue and the profit bridge is arithmetically coherent;
- every material factual input has a source and date;
- the selected industry archetype fits each material segment;
- the cycle, supply/demand, and price assumptions are explicit and logically consistent;
- upstream, downstream, and competitor evidence is connected to a quantified company driver;
- each forecast year has a distinct, causal driver path rather than a copied growth rate;
- year-three demand, market share, margin, and capital needs are bounded by a plausible industry steady state;
- earnings growth that relies on new capacity, market share, or funding has a corresponding feasibility check;
- valuation-bound forecasts contain separate F1–F3 bear net profit, average equity, average assets, ROE and ROA values, and ROE/ROA reconcile arithmetically;
- assumptions are labelled as assumptions rather than facts;
- the conclusion distinguishes a market-price reaction from an operating forecast;
- the response contains no buy, sell, or target-price recommendation.

## Response format

Use this structure unless the user asks for another format:

1. **Scope and cutoff** — company, reporting period, currency, accounting basis, and source cutoff.
2. **Forecast summary** — a table of historical actuals and bear/base/bull revenue, margin, operating profit, net profit, and EPS where applicable. For a three-year request, include current fiscal year plus the next two fiscal years and clearly identify any part-actual year.
3. **Driver tree** — a compact table of driver, baseline, assumption, mechanism, evidence, and confidence. Include the selected industry archetype.
4. **Industry chain and cycle check** — end-market demand, upstream inputs, supply/capacity, inventory, pricing/competition, policy, and execution findings that materially affect the forecast.
5. **Multi-year bridge** — for a horizon above one year, show how demand, price, share, capacity, costs, capex, and the cycle regime change from year one through year three.
6. **Scenario triggers and risks** — what would invalidate or move the base case.
7. **Source list** — direct links, publication dates, and whether each is primary or secondary.

When the result will feed valuation or position sizing, append:

```yaml
forecast_handoff:
  schema_version: "1.1"
  evidence_cutoff: YYYY-MM-DD
  company:
  security:
  upstream_research_status: pass | conditional | fail | insufficient | missing | skipped_by_scope
  forecast_status: usable | conditional | unusable | non_actionable
  horizon:
  accounting_basis:
  bear:
    revenue:
    net_profit:
    eps:
    roe_percent:
    roa_percent:
    years:
      - fiscal_year:
        revenue:
        net_profit:
        eps:
        average_attributable_equity:
        average_total_assets:
        roe_percent:
        roa_percent:
    current_weak_run_rate:
      period:
      roe_percent:
      roa_percent:
      basis:
  base:
    revenue:
    net_profit:
    eps:
    roe_percent:
    roa_percent:
    years:
      - fiscal_year:
        revenue:
        net_profit:
        eps:
        average_attributable_equity:
        average_total_assets:
        roe_percent:
        roa_percent:
  bull:
    revenue:
    net_profit:
    eps:
    roe_percent:
    roa_percent:
    years:
      - fiscal_year:
        revenue:
        net_profit:
        eps:
        average_attributable_equity:
        average_total_assets:
        roe_percent:
        roa_percent:
  balance_sheet_path_status: usable | conditional | missing
  confidence: high | medium | low
  invalidation_triggers: []
  eligible_next_step: valuation | remediation_only
```

`forecast_status: usable` means the forecast skill has calculated and reconciled its outputs from dated source facts and explicitly stated scenario inputs. Forecast ROE／ROA are calculated model results, not directly assumed ROE／ROA or reported facts; do not reject them solely because future operating or capital inputs are scenarios. A full actionable pipeline also requires an upstream research pass; `quick_valuation` may consume the valuation-only exception above. Unknown numeric fields stay empty.

Use ranges, directional language, or an insufficient-evidence conclusion when inputs cannot support precise numerical estimates.
