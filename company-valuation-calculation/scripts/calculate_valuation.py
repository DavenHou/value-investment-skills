#!/usr/bin/env python3
"""Deterministic calculator for the market-earnings-rate framework.

Use the explicit TTM inputs for the stable-company current snapshot. Generic
PE/ROE inputs remain available for normalized scenarios and backward
compatibility, but are labelled as non-TTM.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def positive(name: str, value: float | None) -> float | None:
    if value is not None and value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def calculate(
    *,
    roe_percent: float | None = None,
    pe: float | None = None,
    roe_ttm_percent: float | None = None,
    pe_ttm: float | None = None,
    pb: float | None = None,
    payout_percent: float | None = None,
    current_price: float | None = None,
    targets: list[float] | None = None,
    base_high_pr: float | None = None,
    tax_percent: float | None = None,
    listing_market: str | None = None,
) -> dict[str, Any]:
    if roe_percent is not None and roe_ttm_percent is not None:
        raise ValueError("provide only one of roe_percent or roe_ttm_percent")
    if pe is not None and pe_ttm is not None:
        raise ValueError("provide only one of pe or pe_ttm")
    if (roe_ttm_percent is None) != (pe_ttm is None):
        raise ValueError("pe_ttm and roe_ttm_percent must be provided together")

    effective_roe = roe_ttm_percent if roe_ttm_percent is not None else roe_percent
    effective_pe = pe_ttm if pe_ttm is not None else pe
    if effective_roe is None:
        raise ValueError("provide roe_ttm_percent for a TTM snapshot or roe_percent for a scenario")

    positive("effective_roe_percent", effective_roe)
    positive("effective_pe", effective_pe)
    positive("pb", pb)
    positive("payout_percent", payout_percent)
    positive("current_price", current_price)
    if effective_pe is None and pb is None:
        raise ValueError("provide at least one of pe or pb")
    if tax_percent is not None and not 0 <= tax_percent < 100:
        raise ValueError("tax_percent must be in [0, 100)")

    base_targets = targets or [0.3, 0.4, 0.5, 0.55, 1.0]
    for target in base_targets:
        positive("target", target)
    if listing_market not in {None, "us", "a", "hk"}:
        raise ValueError("listing_market must be one of: us, a, hk")
    market_pr_factor = 0.8 if listing_market == "hk" else 1.0
    targets = [round(target * market_pr_factor, 10) for target in base_targets]

    base: dict[str, float] = {}
    if effective_pe is not None:
        pe_key = "from_pe_ttm" if pe_ttm is not None else "from_pe"
        base[pe_key] = effective_pe / effective_roe
    if pb is not None:
        base["from_pb"] = 100.0 * pb / (effective_roe**2)
    if effective_pe is not None and pb is not None:
        base["from_pe_pb_identity"] = effective_pe**2 / (100.0 * pb)
        base["implied_roe_percent_from_pe_pb"] = 100.0 * pb / effective_pe

    n = None
    if payout_percent is not None:
        n = min(2.0, max(1.0, 50.0 / payout_percent))

    adjusted = None
    if n is not None:
        adjusted = {
            key: value * n
            for key, value in base.items()
            if key.startswith("from_")
        }

    fair_multiples = {
        "pe_at_pr_1": effective_roe,
        "pb_at_pr_1": effective_roe**2 / 100.0,
    }
    if n is not None:
        fair_multiples.update(
            {
                "pe_at_adjusted_pr_1": effective_roe / n,
                "pb_at_adjusted_pr_1": effective_roe**2 / (100.0 * n),
            }
        )

    target_map: dict[str, Any] = {}
    for target in targets:
        entry: dict[str, Any] = {
            "target_pe_base": target * effective_roe,
            "target_pb_base": target * effective_roe**2 / 100.0,
        }
        if n is not None:
            entry["target_pe_adjusted"] = target * effective_roe / n
            entry["target_pb_adjusted"] = target * effective_roe**2 / (100.0 * n)
        if current_price is not None:
            entry["prices_from_base_pr"] = {
                key: current_price * target / value
                for key, value in base.items()
                if key.startswith("from_")
            }
            if adjusted is not None:
                entry["prices_from_adjusted_pr"] = {
                    key: current_price * target / value
                    for key, value in adjusted.items()
                }
        target_map[str(target)] = entry

    after_tax_high = None
    if base_high_pr is not None:
        positive("base_high_pr", base_high_pr)
        after_tax_high = base_high_pr
        if tax_percent is not None:
            after_tax_high *= 1.0 - tax_percent / 100.0

    return {
        "inputs": {
            "roe_percent": roe_percent,
            "roe_ttm_percent": roe_ttm_percent,
            "pe": pe,
            "pe_ttm": pe_ttm,
            "pb": pb,
            "payout_percent": payout_percent,
            "current_price": current_price,
            "base_targets": base_targets,
            "market_adjusted_targets": targets,
            "base_high_pr": base_high_pr,
            "tax_percent": tax_percent,
            "listing_market": listing_market,
            "market_pr_factor": market_pr_factor,
        },
        "calculation_basis": "aligned_ttm" if pe_ttm is not None else "normalized_or_unspecified_period",
        "base_pr": base,
        "payout_adjustment_n": n,
        "adjusted_pr": adjusted,
        "fair_multiples": fair_multiples,
        "after_tax_high_pr_heuristic": after_tax_high,
        "target_map": target_map,
    }


def parse_targets(raw: str) -> list[float]:
    try:
        return [float(item.strip()) for item in raw.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("targets must be comma-separated numbers") from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate PR metrics. Enter ROE as percentage points: 31% -> 31."
    )
    roe_group = parser.add_mutually_exclusive_group(required=True)
    roe_group.add_argument("--roe-ttm-percent", type=float)
    roe_group.add_argument("--roe-percent", type=float)
    pe_group = parser.add_mutually_exclusive_group()
    pe_group.add_argument("--pe-ttm", type=float)
    pe_group.add_argument("--pe", type=float)
    parser.add_argument("--pb", type=float)
    parser.add_argument("--payout-percent", type=float)
    parser.add_argument("--current-price", type=float)
    parser.add_argument(
        "--targets", type=parse_targets, default=parse_targets("0.3,0.4,0.5,0.55,1.0")
    )
    parser.add_argument("--base-high-pr", type=float)
    parser.add_argument("--tax-percent", type=float)
    parser.add_argument("--listing-market", choices=("us", "a", "hk"))
    args = parser.parse_args()

    try:
        result = calculate(
            roe_percent=args.roe_percent,
            pe=args.pe,
            roe_ttm_percent=args.roe_ttm_percent,
            pe_ttm=args.pe_ttm,
            pb=args.pb,
            payout_percent=args.payout_percent,
            current_price=args.current_price,
            targets=args.targets,
            base_high_pr=args.base_high_pr,
            tax_percent=args.tax_percent,
            listing_market=args.listing_market,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
