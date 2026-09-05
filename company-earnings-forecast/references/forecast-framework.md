# Universal forecast framework

## Evidence hierarchy

Use the highest available source for each input.

1. Audited filings, earnings releases, regulatory disclosures, and official company guidance.
2. Earnings-call transcripts, investor presentations, official operating data, named government or regulator statistics.
3. Direct customer, supplier, or competitor disclosures; credible trade associations.
4. Reputable financial media and analyst commentary for context only; do not use it as sole support for a material forecast driver.

Record the date, period covered, unit, currency, and whether a figure is reported, adjusted, management guidance, or an analyst assumption. Apply the same accounting basis across the bridge.

## First principle: select the right economic unit

Start with the company disclosure structure and the industry's economic unit. A useful forecast has a measurable cause before it has a financial output. See `industry-archetypes.md` for industry-specific choices.

Use separate trees for segments whose demand, pricing, or margin formation differs materially. Reconcile segment forecasts to consolidated revenue, eliminations, and the stated accounting basis.

## Revenue driver tree

Use the disclosure structure first. A general form is:

```
Revenue = Σ(segment revenue)
Segment revenue = volume × realised price × mix / FX conversion
```

For each material segment, test these questions:

| Driver | Questions | Useful evidence |
|---|---|---|
| Volume / demand | Is end-market demand rising or falling? Are orders, backlog, traffic, units, subscribers, shipments, or utilisation changing? | Company KPIs, customer data, industry volumes, order commentary |
| Price | Is the company raising price, discounting, or renewing contracts at a new rate? | Management commentary, channel checks, industry price data |
| Mix | Are product, customer, region, or channel shares moving? | Segment disclosures, product data, customer concentration |
| FX | Which reported currencies and exposures matter? | Filing sensitivity tables and segment geography |
| Policy | Does a subsidy, tariff, quota, regulation, or procurement rule change customer economics? | Primary government and company disclosures |

Do not treat a policy headline as a forecast result. Trace the chain: policy → customer economics/demand → company volume or price → revenue → margin.

## Industry chain and cycle test

Make the industry transmission path explicit:

```text
input availability/cost → industry supply, capacity, and inventory → end-market demand and customer orders → company volume, realised price, mix, and utilisation → margin and earnings
```

For each material node, record the indicator, date, source, direction, expected lag, and connection to a company forecast input. Do not use a sector statistic merely because it is correlated with revenue.

| Question | Evidence to test | Forecast implication |
|---|---|---|
| Is demand changing? | Customer sales, orders, backlog, traffic, production, consumption, tendering | Company volume/activity, often with a lag |
| Is supply changing? | Capacity additions, utilisation, closures, inventories, delivery time | Price, share, fixed-cost absorption |
| Is the market discounting? | Realised unit prices, contract resets, competitor commentary, gross-margin dispersion | Price and margin, distinct from demand |
| Are costs moving? | Commodity/component/energy/freight/labour, hedging, pass-through clauses | Unit cost and gross margin |
| Is the cycle turning? | Orders versus sales, inventory days, utilisation, lead time, capex | Direction and timing, not automatic magnitude |

Classify the regime only when supported by evidence: recovery/restocking, expansion/tight supply, peak, correction/destocking, or overcapacity/price war. State uncertainty when indicators conflict.

## Profit bridge

Use a transparent bridge:

```
Gross profit = revenue − cost of revenue
Operating profit = gross profit − operating expenses
Pre-tax profit = operating profit ± net financial / other items
Net profit = pre-tax profit − tax
EPS = net profit attributable to common shareholders / diluted weighted-average shares
```

Separate variable and fixed costs. At minimum, check the following:

| Area | Forecast checks |
|---|---|
| Inputs | Commodity, component, energy, logistics, labour, and supplier bargaining power |
| Capacity | New plants, closures, utilisation, depreciation, idle cost, and operating leverage |
| Competition | Price wars, competitor capacity, inventory correction, and loss of share |
| Opex | Sales commissions, R&D, headcount, marketing, and restructuring |
| Non-operating | FX, interest, tax rate, minority interest, share count, fair value, and one-offs |

Use sensitivity rather than unsupported precision when fixed-cost leverage, commodity cost, or FX is material. For banks, insurers, brokers, and asset managers, substitute the appropriate earning-assets, yield, funding, fee, loss-ratio, credit-cost, assets-under-management, and capital bridge.

## Five-force operating check

| Force | Earnings implication |
|---|---|
| Suppliers | Input cost, continuity of supply, and gross-margin pressure |
| Customers | Volume visibility, price concessions, contract risk, and receivables |
| Existing rivalry | Discounting, share loss, inventory, and lower utilisation |
| New entrants | Future supply, pricing pressure, and incremental capex need |
| Substitutes | Demand destruction, product obsolescence, and R&D burden |

Add management execution, product competitiveness, capacity discipline, and regulation as separate checks. These are diagnostic prompts, not automatic bearish signals.

## Scenario discipline

Build scenarios around causal differences, not arbitrary percentage changes.

| Case | Use when | Example change |
|---|---|---|
| Bear | Demand weakens, pricing pressure rises, or costs/capacity worsen | Lower volume, lower realised price, and negative operating leverage |
| Base | Latest evidence and guidance hold broadly | Volume and margin follow visible drivers |
| Bull | A defined upside trigger occurs | Demand recovery, better mix, or cost relief without a new competitive offset |

For each case, list the 2–5 changed assumptions, the observable trigger, and the data that would confirm or falsify it. Keep policy, macro, and commodity outcomes conditional unless the evidence supports a quantified assumption.

## Minimum model ledger

Maintain a compact ledger for every material input:

| Item | Actual/assumption | Period and unit | Source/date | Transmission path | Confidence |
|---|---|---|---|---|---|
| End-market activity |  |  |  | → company volume |  |
| Realised price/rate |  |  |  | → revenue and margin |  |
| Cost/input/yield |  |  |  | → unit cost or spread |  |
| Capacity/inventory/utilisation |  |  |  | → price and fixed costs |  |
| Share/mix |  |  |  | → volume and margin |  |
| Non-operating item |  |  |  | → net profit only |  |

## Common failure modes

- Use the latest headline without verifying the reporting period or accounting basis.
- Confuse revenue growth with profit growth despite fixed costs or margin shifts.
- Treat market-price movement as proof of an earnings change.
- Use a competitor or sector trend without showing the transmission path to the company.
- Copy management guidance without identifying its assumptions or downside risks.
- Give a single precise forecast when revenue drivers are not observable.
- Treat a fast-growing industry as proof of company pricing power.
- Treat lower raw-material cost as margin expansion without testing customer pass-through or competitive pricing.
- Call every price decline a price war without checking mix, FX, contract timing, and commodity pass-through.
- Extend a near-term growth rate, cycle position, or margin unchanged into years two and three.
- Forecast profit growth from capacity, share, or capex without testing timing, funding, utilisation, depreciation, and cash conversion.
