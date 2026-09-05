# Three-year forecast framework

Use this reference whenever the forecast horizon is more than one fiscal year.

## Fiscal-year convention and granularity

For a request for the "next three years," use the current fiscal year plus the following two fiscal years unless the user specifies three full future fiscal years. Mark the current year as part actual and part forecast. State the fiscal-year end, data cutoff, and whether the output is annual or quarterly.

Forecast the current and next fiscal year at quarterly detail only when the evidence supports it. Forecast the third year annually by default. Extra decimal precision in year three is not evidence.

## Build three separate annual paths

| Period | What may be forecast with relative confidence | Required checks |
|---|---|---|
| Year 1 | Orders, backlog, current activity, announced products, pricing, near-term capacity | Latest actuals, guidance, customer demand, inventory, cost and FX sensitivity |
| Year 2 | Cycle progression, capacity start-up, product adoption, contract renewal, share evolution | Industry supply/demand, competitor capex, utilisation, product roadmap, capex and depreciation timing |
| Year 3 | Normalised industry growth, sustainable share, mature margins, capital intensity | Market-size constraint, steady-state margin, return on capital, balance-sheet and regulation feasibility |

Do not repeat Year 1 growth, price, or margin assumptions mechanically. Name the changed assumptions and the event or condition that creates each change.

## Revenue, margin, and capital bridge

Use the economic unit appropriate to the industry. A general multi-year structure is:

```text
Company volume_t = end-market activity_t × company share_t
Revenue_t = volume_t × realised price_t × mix_t ± FX_t
Gross profit_t = revenue_t − variable cost_t − fixed cost_t
Capacity_t+1 = capacity_t + commissioned capex_t − closures_t
```

For asset-heavy businesses, make the sequence explicit: capex commitment → construction/approval → capacity start-up → utilisation → revenue → depreciation and cash flow. Do not credit revenue or margin before capacity is realistically available.

For asset-light businesses, substitute hiring, distribution, product launches, customer acquisition, or regulated rate recovery for physical capacity. For financial companies, bridge balance-sheet growth, spreads, fees, credit losses, capital, and funding rather than gross margin.

## Steady-state guardrails

Apply these checks to years two and three:

- Reconcile company unit growth with a sourced end-market size and a stated share change. A company cannot indefinitely grow faster than its market without gaining share.
- Test whether share gains require lower price, higher sales expense, additional capacity, distribution, or a product advantage.
- Bound revenue growth by market maturity, replacement cycles, regulation, and supply additions; label an unobservable structural change as an assumption.
- Reconcile margin with price, mix, input costs, utilisation, and competitor conduct. Do not assume cost deflation belongs entirely to the company.
- Compare mature margins and capital intensity with the company's history and relevant industry evidence. Explain any persistent divergence.
- Where material, reconcile earnings with capex, working capital, debt service, tax, and capital requirements; a profit forecast alone is incomplete if funding capacity is binding.

## Cycle phasing

State the estimated regime for each forecast year: recovery/restocking, expansion/tight supply, peak, correction/destocking, overcapacity/price war, or stable maturity. Give the observable signal that would move the case to another regime.

Use lags explicitly. Examples: new capacity may depress utilisation before it creates revenue; lower commodity costs may affect contract price after a reset; an order recovery may precede recognised revenue; policy may affect demand only after implementation.

## Three-year scenarios

Keep the causal differences coherent across years.

| Case | Year 1 | Years 2–3 |
|---|---|---|
| Bear | Current demand, price, cost, or execution downside appears | Recovery is delayed, share weakens, capacity is under-utilised, or funding/capital pressure persists |
| Base | Visible drivers and disclosed plans broadly hold | Cycle normalises; share, margin, and capital intensity converge toward defensible levels |
| Bull | A named upside trigger improves volume, mix, or cost | Advantage persists only if evidence supports durable share, capacity, and pricing power |

Do not assign a probability unless the user provides one or a defensible method exists. Show a range or lower confidence rather than an unsupported point estimate for year three.

## Required output for three-year requests

Include an annual table with revenue, growth, key unit/volume driver, realised price or rate, gross or operating margin, net profit, and EPS where relevant. Add capex, free cash flow, debt, or capital metrics when they materially constrain earnings.

Then provide a concise multi-year bridge showing, for each year, the cycle regime, changed drivers, primary evidence, key risk, and confidence. Identify which Year 1 actual release or leading indicator will cause the forecast to be revised first.
