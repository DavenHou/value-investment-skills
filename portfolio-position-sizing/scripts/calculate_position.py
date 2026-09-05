#!/usr/bin/env python3
"""Deterministic stress-loss position limit calculator.

All percentage arguments use percentage points: 1 means 1%, 30 means 30%.
This script only performs arithmetic. The skill applies fundamental/valuation gates.
"""

import argparse
import json
import math
from typing import Optional


def percentage(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0 or number > 100:
        raise argparse.ArgumentTypeError("percentage must be between 0 and 100")
    return number


def positive_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def stock_count(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("stock count cannot be negative")
    return number


def tranche(value: str) -> tuple[float, float]:
    """Parse a cash allocation and execution price as WEIGHT@PRICE."""
    try:
        weight_text, price_text = value.split("@", 1)
        weight = percentage(weight_text)
        price = positive_number(price_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("tranche must be WEIGHT@PRICE, e.g. 4@45.45") from exc
    return weight, price


def optional_min(values: list[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def money(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(value, 2)


def pct(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(value, 4)


def ladder_stress(tranches: list[tuple[float, float]], stress_price: float) -> dict:
    """Return completed-ladder and per-tranche stress using cash allocations."""
    total_weight = sum(weight for weight, _ in tranches)
    shares_per_portfolio_percent = sum(weight / price for weight, price in tranches)
    weighted_average_cost = total_weight / shares_per_portfolio_percent
    per_tranche = [
        {
            "allocation_percent": pct(weight),
            "entry_price": money(price),
            "loss_percent_of_tranche": pct((1 - stress_price / price) * 100),
            "loss_percent_of_portfolio": pct(weight * (1 - stress_price / price)),
        }
        for weight, price in tranches
    ]
    portfolio_loss = sum(item["loss_percent_of_portfolio"] for item in per_tranche)
    return {
        "stress_price": money(stress_price),
        "completed_ladder_weighted_average_cost": money(weighted_average_cost),
        "completed_ladder_loss_percent": pct((1 - stress_price / weighted_average_cost) * 100),
        "completed_ladder_loss_percent_of_portfolio": pct(portfolio_loss),
        "per_tranche": per_tranche,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate a position cap from portfolio stress-loss budget."
    )
    parser.add_argument("--portfolio-value", type=positive_number)
    parser.add_argument("--risk-budget-percent", required=True, type=percentage)
    parser.add_argument("--stress-loss-low-percent", required=True, type=percentage)
    parser.add_argument("--stress-loss-high-percent", required=True, type=percentage)
    parser.add_argument("--current-weight-percent", type=percentage)
    parser.add_argument("--single-name-cap-percent", type=percentage, default=35.0)
    parser.add_argument("--valuation-suggested-cap-percent", type=percentage)
    parser.add_argument("--listing-market", choices=("us", "a", "hk"))
    parser.add_argument("--market-preference-factor", type=percentage)
    parser.add_argument("--current-stock-count", type=stock_count)
    parser.add_argument("--qualified-undervalued-count", type=stock_count)
    parser.add_argument("--preferred-stock-count-low", type=stock_count, default=5)
    parser.add_argument("--preferred-stock-count-target", type=stock_count, default=6)
    parser.add_argument("--preferred-stock-count-high", type=stock_count, default=8)
    parser.add_argument("--maximum-stock-count", type=stock_count)
    parser.add_argument("--new-position", action="store_true")
    parser.add_argument("--industry-remaining-cap-percent", type=percentage)
    parser.add_argument("--correlation-remaining-cap-percent", type=percentage)
    parser.add_argument("--liquidity-cap-percent", type=percentage)
    parser.add_argument("--account-cap-percent", type=percentage)
    parser.add_argument(
        "--tranche", action="append", type=tranche, metavar="WEIGHT@PRICE",
        help="planned cash allocation and execution price; repeat for each filled tranche",
    )
    parser.add_argument("--stress-price-low", type=positive_number)
    parser.add_argument("--stress-price-high", type=positive_number)
    args = parser.parse_args()

    low = args.stress_loss_low_percent
    high = args.stress_loss_high_percent
    if low <= 0 or high <= 0:
        parser.error("stress loss percentages must be greater than zero")
    if low > high:
        parser.error("stress-loss-low-percent cannot exceed stress-loss-high-percent")
    if args.maximum_stock_count is not None and args.maximum_stock_count <= 0:
        parser.error("maximum-stock-count must be greater than zero")
    if args.preferred_stock_count_low <= 0:
        parser.error("preferred-stock-count-low must be greater than zero")
    if args.preferred_stock_count_low > args.preferred_stock_count_high:
        parser.error("preferred-stock-count-low cannot exceed preferred-stock-count-high")
    if not args.preferred_stock_count_low <= args.preferred_stock_count_target <= args.preferred_stock_count_high:
        parser.error("preferred-stock-count-target must be within the preferred range")
    stress_prices = (args.stress_price_low, args.stress_price_high)
    if any(value is not None for value in stress_prices) and (
        not args.tranche or any(value is None for value in stress_prices)
    ):
        parser.error("--tranche and both --stress-price-low/--stress-price-high must be supplied together")
    if args.stress_price_low is not None and args.stress_price_low > args.stress_price_high:
        parser.error("stress-price-low cannot exceed stress-price-high")

    # HK's general market discount is applied to PR thresholds upstream. Keep
    # the default position factor at 100% to avoid counting the same risk twice.
    default_market_factors = {"us": 100.0, "a": 90.0, "hk": 100.0}
    market_factor_percent = args.market_preference_factor
    if market_factor_percent is None and args.listing_market is not None:
        market_factor_percent = default_market_factors[args.listing_market]
    market_factor_percent = 100.0 if market_factor_percent is None else market_factor_percent
    market_adjusted_valuation_cap = (
        None
        if args.valuation_suggested_cap_percent is None
        else args.valuation_suggested_cap_percent * market_factor_percent / 100
    )

    conservative_formula_cap = args.risk_budget_percent / high * 100
    sensitivity_formula_cap = args.risk_budget_percent / low * 100

    named_caps = {
        "risk_budget": conservative_formula_cap,
        "valuation_suggested_market_adjusted": market_adjusted_valuation_cap,
        "single_name": args.single_name_cap_percent,
        "industry_remaining": args.industry_remaining_cap_percent,
        "correlation_remaining": args.correlation_remaining_cap_percent,
        "liquidity": args.liquidity_cap_percent,
        "account": args.account_cap_percent,
    }
    effective_cap = optional_min(list(named_caps.values()))
    binding = [
        name
        for name, value in named_caps.items()
        if value is not None and math.isclose(value, effective_cap, rel_tol=1e-12, abs_tol=1e-12)
    ]

    current_weight = args.current_weight_percent
    current_stress_loss = None if current_weight is None else current_weight * high / 100
    remaining_capacity = (
        None if current_weight is None else max(0.0, effective_cap - current_weight)
    )
    over_cap = None if current_weight is None else current_weight > effective_cap
    projected_stock_count = (
        None
        if args.current_stock_count is None
        else args.current_stock_count + (1 if args.new_position else 0)
    )
    if projected_stock_count is None:
        stock_count_assessment = "unknown"
        slot_available = None
    elif args.maximum_stock_count is not None and projected_stock_count > args.maximum_stock_count:
        stock_count_assessment = "above_user_hard_cap"
        slot_available = False
    elif projected_stock_count < args.preferred_stock_count_low:
        stock_count_assessment = "below_preferred_range_cash_allowed"
        slot_available = True
    elif projected_stock_count == args.preferred_stock_count_target:
        stock_count_assessment = "at_neutral_target"
        slot_available = True
    elif projected_stock_count <= args.preferred_stock_count_high:
        stock_count_assessment = "within_preferred_range"
        slot_available = True
    elif (
        args.qualified_undervalued_count is not None
        and args.qualified_undervalued_count >= projected_stock_count
    ):
        stock_count_assessment = "above_preferred_but_opportunity_supported"
        slot_available = True
    else:
        stock_count_assessment = "replacement_or_diversification_case_required"
        slot_available = False

    result = {
        "inputs": {
            "portfolio_value": args.portfolio_value,
            "risk_budget_percent": args.risk_budget_percent,
            "stress_loss_low_percent": low,
            "stress_loss_high_percent": high,
            "current_weight_percent": current_weight,
            "valuation_suggested_cap_percent": args.valuation_suggested_cap_percent,
            "listing_market": args.listing_market,
            "market_preference_factor_percent": market_factor_percent,
            "market_adjusted_valuation_cap_percent": pct(market_adjusted_valuation_cap),
            "current_stock_count": args.current_stock_count,
            "qualified_undervalued_count": args.qualified_undervalued_count,
            "preferred_stock_count_low": args.preferred_stock_count_low,
            "preferred_stock_count_target": args.preferred_stock_count_target,
            "preferred_stock_count_high": args.preferred_stock_count_high,
            "maximum_stock_count": args.maximum_stock_count,
            "new_position": args.new_position,
        },
        "conservative_formula_cap_percent": pct(conservative_formula_cap),
        "sensitivity_formula_cap_percent": pct(sensitivity_formula_cap),
        "effective_cap_percent": pct(effective_cap),
        "binding_constraint": binding,
        "current_stress_loss_percent_of_portfolio": pct(current_stress_loss),
        "remaining_capacity_percent": pct(remaining_capacity),
        "current_position_over_cap": over_cap,
        "new_position_slot_available": slot_available,
        "projected_stock_count": projected_stock_count,
        "stock_count_assessment": stock_count_assessment,
        "risk_budget_amount": money(
            None
            if args.portfolio_value is None
            else args.portfolio_value * args.risk_budget_percent / 100
        ),
        "effective_cap_amount": money(
            None
            if args.portfolio_value is None
            else args.portfolio_value * effective_cap / 100
        ),
        "current_stress_loss_amount": money(
            None
            if args.portfolio_value is None or current_stress_loss is None
            else args.portfolio_value * current_stress_loss / 100
        ),
        "tranche_stress": (
            None
            if not args.tranche
            else {
                "total_planned_weight_percent": pct(sum(weight for weight, _ in args.tranche)),
                "lower_stress": ladder_stress(args.tranche, args.stress_price_low),
                "higher_stress": ladder_stress(args.tranche, args.stress_price_high),
                "path_risk_note": (
                    "Only completed tranches are included. Unfilled lower-price tranches do not "
                    "reduce the loss on already-filled capital if the price gaps to stress."
                ),
            }
        ),
        "note": "Arithmetic only; apply fundamental, valuation, evidence, and review gates separately.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
