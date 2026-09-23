#!/usr/bin/env python3
"""Deterministic position, completed-ladder drawdown, and optional Kelly calculator.

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


def long_only_loss_multiple(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > 1:
        raise argparse.ArgumentTypeError("long-only loss multiple must be greater than zero and at most one")
    return number


def kelly_fraction(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > 1:
        raise argparse.ArgumentTypeError("Kelly fraction must be greater than zero and at most one")
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


def kelly_scenario(value: str) -> tuple[float, float]:
    """Parse a probability percentage and total-return multiple as PROBABILITY@RETURN."""
    try:
        probability_text, return_text = value.split("@", 1)
        probability = percentage(probability_text)
        return_multiple = float(return_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Kelly scenario must be PROBABILITY_PERCENT@RETURN_MULTIPLE, e.g. 50@-1"
        ) from exc
    if not math.isfinite(return_multiple) or return_multiple < -1:
        raise argparse.ArgumentTypeError("long-only scenario return must be finite and at least -1")
    return probability, return_multiple


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


def long_only_log_optimal_fraction(scenarios: list[tuple[float, float]]) -> float:
    """Maximize expected log growth for calibrated scenarios with 0 <= fraction <= 1."""
    probabilities = [probability / 100 for probability, _ in scenarios]
    returns = [return_multiple for _, return_multiple in scenarios]
    expected_return = sum(probability * return_multiple for probability, return_multiple in zip(probabilities, returns))
    if expected_return <= 0:
        return 0.0

    upper = 1.0
    for return_multiple in returns:
        if return_multiple < 0:
            upper = min(upper, -1 / return_multiple)
    safe_upper = math.nextafter(upper, 0.0)

    def derivative(fraction: float) -> float:
        return sum(
            probability * return_multiple / (1 + fraction * return_multiple)
            for probability, return_multiple in zip(probabilities, returns)
        )

    if derivative(safe_upper) >= 0:
        return safe_upper

    low, high = 0.0, safe_upper
    for _ in range(200):
        midpoint = (low + high) / 2
        if derivative(midpoint) > 0:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def build_kelly_reference(args: argparse.Namespace, parser: argparse.ArgumentParser) -> tuple[dict, Optional[float]]:
    binary_values = (
        args.kelly_win_probability_percent,
        args.kelly_win_return_multiple,
        args.kelly_loss_return_multiple,
    )
    has_binary = any(value is not None for value in binary_values)
    has_multi = bool(args.kelly_scenario)
    if has_binary and not all(value is not None for value in binary_values):
        parser.error("all three binary Kelly inputs must be supplied together")
    if has_binary and has_multi:
        parser.error("binary Kelly inputs and --kelly-scenario are mutually exclusive")

    has_model = has_binary or has_multi
    if args.kelly_status in ("usable", "illustrative") and not has_model:
        parser.error("usable or illustrative Kelly status requires a binary or multi-scenario model")
    if args.kelly_status in ("not_usable", "not_applicable") and has_model:
        parser.error("Kelly model inputs require status usable or illustrative")
    if args.kelly_status == "illustrative" and args.kelly_input_basis is None:
        parser.error("illustrative Kelly status requires --kelly-input-basis")
    if args.kelly_adopted_fraction is not None and args.kelly_status != "usable":
        parser.error("an adopted Kelly fraction requires --kelly-status usable")
    if args.kelly_blocking_reason and args.kelly_status != "not_usable":
        parser.error("Kelly blocking reasons require --kelly-status not_usable")

    audit_fields = (
        args.kelly_strategy_scope,
        args.kelly_sample_cutoff_date,
        args.kelly_probability_source,
        args.kelly_probability_confidence_method,
        args.kelly_payoff_conservative_method,
        args.kelly_horizon,
        args.kelly_exit_rule,
        args.kelly_raw_sample_size,
        args.kelly_effective_sample_size,
    )
    if args.kelly_status == "usable":
        if args.kelly_input_basis != "conservative":
            parser.error("usable Kelly status requires --kelly-input-basis conservative")
        if any(value is None or value == "" for value in audit_fields):
            parser.error("usable Kelly status requires complete sample, cutoff, horizon, source, and exit audit fields")
        if args.kelly_raw_sample_size <= 0 or args.kelly_effective_sample_size <= 0:
            parser.error("usable Kelly sample sizes must be greater than zero")
        if args.kelly_effective_sample_size > args.kelly_raw_sample_size:
            parser.error("effective Kelly sample size cannot exceed raw sample size")

    base = {
        "status": args.kelly_status,
        "outcome_model": None,
        "input_basis": args.kelly_input_basis,
        "strategy_scope": args.kelly_strategy_scope,
        "horizon": args.kelly_horizon,
        "exit_rule": args.kelly_exit_rule,
        "probability_source": args.kelly_probability_source,
        "probability_confidence_method": args.kelly_probability_confidence_method,
        "payoff_conservative_method": args.kelly_payoff_conservative_method,
        "sample_cutoff_date": args.kelly_sample_cutoff_date,
        "raw_sample_size": args.kelly_raw_sample_size,
        "effective_sample_size": args.kelly_effective_sample_size,
        "scenarios": [],
        "expected_edge_multiple": None,
        "unconstrained_full_kelly_percent": None,
        "full_kelly_long_only_percent": None,
        "half_kelly_percent": None,
        "quarter_kelly_percent": None,
        "adopted_fraction": args.kelly_adopted_fraction,
        "adopted_cap_percent": None,
        "cap_active": False,
        "blocking_reasons": [],
    }
    if not has_model:
        if args.kelly_status == "not_usable":
            base["blocking_reasons"] = args.kelly_blocking_reason or ["calibrated_inputs_missing"]
        return base, None

    unconstrained_fraction: Optional[float]
    if has_binary:
        probability = args.kelly_win_probability_percent / 100
        if probability <= 0 or probability >= 1:
            parser.error("binary Kelly win probability must be greater than 0 and less than 100")
        win_return = args.kelly_win_return_multiple
        loss_return = args.kelly_loss_return_multiple
        expected_edge = probability * win_return - (1 - probability) * loss_return
        unconstrained_fraction = expected_edge / (win_return * loss_return)
        scenarios = [
            (args.kelly_win_probability_percent, win_return),
            (100 - args.kelly_win_probability_percent, -loss_return),
        ]
        long_only_fraction = min(1.0, max(0.0, unconstrained_fraction))
        base["outcome_model"] = "binary"
    else:
        scenarios = args.kelly_scenario
        if len(scenarios) < 2:
            parser.error("multi-scenario Kelly requires at least two scenarios")
        if any(probability <= 0 for probability, _ in scenarios):
            parser.error("multi-scenario Kelly probabilities must all be greater than zero")
        if not math.isclose(sum(probability for probability, _ in scenarios), 100.0, abs_tol=1e-8):
            parser.error("multi-scenario Kelly probabilities must sum to 100")
        if not any(return_multiple > 0 for _, return_multiple in scenarios) or not any(
            return_multiple < 0 for _, return_multiple in scenarios
        ):
            parser.error("multi-scenario Kelly requires at least one positive and one negative return")
        expected_edge = sum(
            probability / 100 * return_multiple for probability, return_multiple in scenarios
        )
        unconstrained_fraction = None
        long_only_fraction = long_only_log_optimal_fraction(scenarios)
        base["outcome_model"] = "multi_scenario"

    full_percent = long_only_fraction * 100
    base.update(
        {
            "scenarios": [
                {"probability_percent": pct(probability), "return_multiple": pct(return_multiple)}
                for probability, return_multiple in scenarios
            ],
            "expected_edge_multiple": pct(expected_edge),
            "unconstrained_full_kelly_percent": pct(
                None if unconstrained_fraction is None else unconstrained_fraction * 100
            ),
            "full_kelly_long_only_percent": pct(full_percent),
            "half_kelly_percent": pct(full_percent / 2),
            "quarter_kelly_percent": pct(full_percent / 4),
        }
    )
    if args.kelly_status == "usable" and args.kelly_adopted_fraction is not None:
        adopted_cap = full_percent * args.kelly_adopted_fraction
        base["adopted_cap_percent"] = pct(adopted_cap)
        base["cap_active"] = True
        return base, adopted_cap
    return base, None


def binding_constraints(named_caps: dict[str, Optional[float]], effective_cap: float) -> list[str]:
    return [
        name
        for name, value in named_caps.items()
        if value is not None and math.isclose(value, effective_cap, rel_tol=1e-12, abs_tol=1e-12)
    ]


def assess_stock_count(
    args: argparse.Namespace, projected_stock_count: Optional[int], *, legacy_rules: bool
) -> tuple[Optional[bool], str]:
    """Return whether a new-position slot is available under the selected rule version."""
    if args.assume_stock_count_within_policy:
        return True, "assumed_within_policy_by_user"
    if projected_stock_count is None:
        return None, "unknown"
    if args.maximum_stock_count is not None and projected_stock_count > args.maximum_stock_count:
        return False, "above_user_hard_cap"
    preferred_low, preferred_target, preferred_high = (
        (6, 8, 10)
        if legacy_rules
        else (
            args.preferred_stock_count_low,
            args.preferred_stock_count_target,
            args.preferred_stock_count_high,
        )
    )
    if projected_stock_count < preferred_low:
        return True, "below_preferred_range_cash_allowed"
    if projected_stock_count == preferred_target:
        return True, "at_neutral_target"
    if projected_stock_count <= preferred_high:
        return True, "within_preferred_range"
    if legacy_rules:
        return False, "replacement_or_diversification_case_required"
    if (
        projected_stock_count <= 10
        and args.above_preferred_expansion_justified
        and args.qualified_undervalued_count is not None
        and args.qualified_undervalued_count >= projected_stock_count
    ):
        return True, "nine_to_ten_exception_evidence_supported"
    if projected_stock_count <= 10:
        return False, "nine_to_ten_replacement_or_risk_improvement_required"
    return False, "above_policy_exception_zone"


def build_rule_comparison(
    *,
    legacy_effective_cap: float,
    legacy_binding: list[str],
    legacy_remaining_capacity: Optional[float],
    legacy_over_cap: Optional[bool],
    legacy_slot_available: Optional[bool],
    legacy_stock_count_assessment: str,
    current_effective_cap: float,
    current_binding: list[str],
    current_remaining_capacity: Optional[float],
    current_over_cap: Optional[bool],
    current_slot_available: Optional[bool],
    current_stock_count_assessment: str,
    current_preferred_stock_count_range: list[int],
    kelly_reference: dict,
) -> dict:
    cap_changed = not math.isclose(
        legacy_effective_cap, current_effective_cap, rel_tol=1e-12, abs_tol=1e-12
    )
    slot_changed = legacy_slot_available != current_slot_available
    active_kelly = kelly_reference["cap_active"]
    kelly_is_binding = "kelly_reference" in current_binding
    if not active_kelly:
        kelly_role = "not_active"
    elif not kelly_is_binding:
        kelly_role = "active_not_binding"
    elif cap_changed and current_effective_cap < legacy_effective_cap:
        kelly_role = "binding_reduced_cap"
    else:
        kelly_role = "binding_without_cap_change"

    reasons = []
    if kelly_role == "binding_reduced_cap":
        reasons.append("active_fractional_kelly_reduced_cap")
    if slot_changed:
        reasons.append("nine_to_ten_evidence_gate_changed_slot")
    if not reasons:
        reasons.append("no_rule_change_effect_on_this_input")

    return {
        "baseline_rule_version": "pre_kelly_pre_evidence_stock_count_v1",
        "comparison_rule_version": "current",
        "old_rules": {
            "preferred_stock_count_range": [6, 10],
            "effective_cap_percent": pct(legacy_effective_cap),
            "binding_constraint": legacy_binding,
            "remaining_capacity_percent": pct(legacy_remaining_capacity),
            "current_position_over_cap": legacy_over_cap,
            "new_position_slot_available": legacy_slot_available,
            "stock_count_assessment": legacy_stock_count_assessment,
        },
        "new_rules": {
            "preferred_stock_count_range": current_preferred_stock_count_range,
            "effective_cap_percent": pct(current_effective_cap),
            "binding_constraint": current_binding,
            "remaining_capacity_percent": pct(current_remaining_capacity),
            "current_position_over_cap": current_over_cap,
            "new_position_slot_available": current_slot_available,
            "stock_count_assessment": current_stock_count_assessment,
        },
        "effective_cap_delta_percent": pct(current_effective_cap - legacy_effective_cap),
        "remaining_capacity_delta_percent": (
            None
            if legacy_remaining_capacity is None or current_remaining_capacity is None
            else pct(current_remaining_capacity - legacy_remaining_capacity)
        ),
        "effective_cap_changed": cap_changed,
        "new_position_slot_changed": slot_changed,
        "kelly_decision_role": kelly_role,
        "kelly_participated_in_final_decision": kelly_role.startswith("binding_"),
        "change_reasons": reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate position caps and validate completed-ladder drawdown."
    )
    parser.add_argument("--portfolio-value", type=positive_number)
    parser.add_argument("--risk-budget-percent", type=percentage)
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
    parser.add_argument(
        "--assume-stock-count-within-policy",
        action="store_true",
        help="Treat the 5-8 stock-count check as satisfied for this run.",
    )
    parser.add_argument("--above-preferred-expansion-justified", action="store_true")
    parser.add_argument(
        "--compare-legacy-rules",
        action="store_true",
        help="Compare pre-Kelly/pre-evidence-stock-count rules with the current rules using identical inputs.",
    )
    parser.add_argument("--industry-remaining-cap-percent", type=percentage)
    parser.add_argument("--correlation-remaining-cap-percent", type=percentage)
    parser.add_argument("--liquidity-cap-percent", type=percentage)
    parser.add_argument("--account-cap-percent", type=percentage)
    parser.add_argument(
        "--kelly-status",
        choices=("usable", "illustrative", "not_usable", "not_applicable"),
        default="not_applicable",
    )
    parser.add_argument(
        "--kelly-input-basis",
        choices=("conservative", "point_estimate", "subjective_scenario"),
    )
    parser.add_argument("--kelly-win-probability-percent", type=percentage)
    parser.add_argument("--kelly-win-return-multiple", type=positive_number)
    parser.add_argument("--kelly-loss-return-multiple", type=long_only_loss_multiple)
    parser.add_argument(
        "--kelly-scenario", action="append", type=kelly_scenario,
        metavar="PROBABILITY_PERCENT@RETURN_MULTIPLE",
    )
    parser.add_argument("--kelly-adopted-fraction", type=kelly_fraction)
    parser.add_argument("--kelly-strategy-scope")
    parser.add_argument("--kelly-sample-cutoff-date")
    parser.add_argument("--kelly-probability-source")
    parser.add_argument("--kelly-probability-confidence-method")
    parser.add_argument("--kelly-payoff-conservative-method")
    parser.add_argument("--kelly-horizon")
    parser.add_argument("--kelly-exit-rule")
    parser.add_argument("--kelly-raw-sample-size", type=stock_count)
    parser.add_argument("--kelly-effective-sample-size", type=stock_count)
    parser.add_argument("--kelly-blocking-reason", action="append")
    parser.add_argument(
        "--tranche", action="append", type=tranche, metavar="WEIGHT@PRICE",
        help="planned cash allocation and execution price; repeat for each filled tranche",
    )
    parser.add_argument("--stress-price-low", type=positive_number)
    parser.add_argument("--stress-price-high", type=positive_number)
    parser.add_argument(
        "--max-completed-position-drawdown-percent",
        type=percentage,
        default=50.0,
        help="Maximum loss on the fully completed ladder, measured from its cash-weighted average cost.",
    )
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

    kelly_reference, active_kelly_cap = build_kelly_reference(args, parser)

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

    conservative_formula_cap = (
        None if args.risk_budget_percent is None else args.risk_budget_percent / high * 100
    )
    sensitivity_formula_cap = (
        None if args.risk_budget_percent is None else args.risk_budget_percent / low * 100
    )

    legacy_named_caps = {
        "risk_budget": conservative_formula_cap,
        "valuation_suggested_market_adjusted": market_adjusted_valuation_cap,
        "single_name": args.single_name_cap_percent,
        "industry_remaining": args.industry_remaining_cap_percent,
        "correlation_remaining": args.correlation_remaining_cap_percent,
        "liquidity": args.liquidity_cap_percent,
        "account": args.account_cap_percent,
    }
    legacy_effective_cap = optional_min(list(legacy_named_caps.values()))
    legacy_binding = binding_constraints(legacy_named_caps, legacy_effective_cap)
    named_caps = {"kelly_reference": active_kelly_cap, **legacy_named_caps}
    effective_cap = optional_min(list(named_caps.values()))
    binding = binding_constraints(named_caps, effective_cap)

    current_weight = args.current_weight_percent
    current_stress_loss = None if current_weight is None else current_weight * high / 100
    remaining_capacity = (
        None if current_weight is None else max(0.0, effective_cap - current_weight)
    )
    legacy_remaining_capacity = (
        None if current_weight is None else max(0.0, legacy_effective_cap - current_weight)
    )
    over_cap = None if current_weight is None else current_weight > effective_cap
    legacy_over_cap = None if current_weight is None else current_weight > legacy_effective_cap
    projected_stock_count = (
        None
        if args.current_stock_count is None
        else args.current_stock_count + (1 if args.new_position else 0)
    )
    slot_available, stock_count_assessment = assess_stock_count(
        args, projected_stock_count, legacy_rules=False
    )
    legacy_slot_available, legacy_stock_count_assessment = assess_stock_count(
        args, projected_stock_count, legacy_rules=True
    )

    tranche_stress = None
    completed_ladder_drawdown_gate = {
        "status": "not_calculated",
        "limit_percent": pct(args.max_completed_position_drawdown_percent),
        "worst_drawdown_percent": None,
        "passed": None,
        "effect": "feasibility_gate_not_position_cap",
    }
    if args.tranche:
        tranche_stress = {
            "total_planned_weight_percent": pct(sum(weight for weight, _ in args.tranche)),
            "lower_stress": ladder_stress(args.tranche, args.stress_price_low),
            "higher_stress": ladder_stress(args.tranche, args.stress_price_high),
            "path_risk_note": (
                "Only completed tranches are included. Unfilled lower-price tranches do not "
                "reduce the loss on already-filled capital if the price gaps to stress."
            ),
        }
        worst_drawdown = max(
            tranche_stress["lower_stress"]["completed_ladder_loss_percent"],
            tranche_stress["higher_stress"]["completed_ladder_loss_percent"],
        )
        completed_ladder_drawdown_gate.update(
            {
                "status": "pass" if worst_drawdown <= args.max_completed_position_drawdown_percent else "fail",
                "worst_drawdown_percent": pct(worst_drawdown),
                "passed": worst_drawdown <= args.max_completed_position_drawdown_percent,
            }
        )

    rule_comparison = None
    if args.compare_legacy_rules:
        rule_comparison = build_rule_comparison(
            legacy_effective_cap=legacy_effective_cap,
            legacy_binding=legacy_binding,
            legacy_remaining_capacity=legacy_remaining_capacity,
            legacy_over_cap=legacy_over_cap,
            legacy_slot_available=legacy_slot_available,
            legacy_stock_count_assessment=legacy_stock_count_assessment,
            current_effective_cap=effective_cap,
            current_binding=binding,
            current_remaining_capacity=remaining_capacity,
            current_over_cap=over_cap,
            current_slot_available=slot_available,
            current_stock_count_assessment=stock_count_assessment,
            current_preferred_stock_count_range=[
                args.preferred_stock_count_low,
                args.preferred_stock_count_high,
            ],
            kelly_reference=kelly_reference,
        )

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
            "above_preferred_expansion_justified": args.above_preferred_expansion_justified,
            "assume_stock_count_within_policy": args.assume_stock_count_within_policy,
            "max_completed_position_drawdown_percent": args.max_completed_position_drawdown_percent,
            "compare_legacy_rules": args.compare_legacy_rules,
        },
        "portfolio_risk_budget_status": (
            "selected" if args.risk_budget_percent is not None else "not_selected_sensitivity_only"
        ),
        "conservative_formula_cap_percent": pct(conservative_formula_cap),
        "sensitivity_formula_cap_percent": pct(sensitivity_formula_cap),
        "effective_cap_percent": pct(effective_cap),
        "binding_constraint": binding,
        "kelly_reference": kelly_reference,
        "rule_comparison": rule_comparison,
        "current_stress_loss_percent_of_portfolio": pct(current_stress_loss),
        "remaining_capacity_percent": pct(remaining_capacity),
        "current_position_over_cap": over_cap,
        "new_position_slot_available": slot_available,
        "projected_stock_count": projected_stock_count,
        "stock_count_assessment": stock_count_assessment,
        "unallocated_capital_policy": "hold_cash_do_not_fill_to_minimum",
        "risk_budget_amount": money(
            None
            if args.portfolio_value is None or args.risk_budget_percent is None
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
        "tranche_stress": tranche_stress,
        "completed_ladder_drawdown_gate": completed_ladder_drawdown_gate,
        "note": "Arithmetic only; apply fundamental, valuation, evidence, and review gates separately.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# 2026-09-13 第三轮定稿：质量分 → 单股仓位上限；并输出最坏情况预估
# ---------------------------------------------------------------------------

QUALITY_LADDER = [
    (85.0, 35.0, "满仓档：只给真正看懂、且各维度均无未决红旗的公司"),
    (78.0, 28.0, "重仓档"),
    (70.0, 20.0, "标准档"),
    (60.0, 10.0, "试仓档：刚过质量闸门，只给小仓位"),
    (55.0, 5.0, "降级候选 pass_downgraded：仍可进下游，但只给 5%"),
]

QUALITY_FLOOR = 55.0  # 第27条（2026-09-18）：能进下游的底线由 60/50 提到 55


def quality_cap(score: float | None) -> dict:
    """把 100 分质量评分映成单股仓位上限。

    闸门：< 55 分不建仓；55–59 分为 `pass_downgraded`，上限 5%。
    上限：35% 绝对硬上限，任何分数都不得突破。

    档位按实际可得分数标定，不按理论满分标定：七维评分卡带上限与否决项，
    现实中最优质的公司通常落在 78–88 分，90 分以上基本不可达。把满仓档
    定在 90 会让 35% 永远是死数；定在 85 才让它偶尔可用。
    """
    if score is None:
        return {"quality_score": None, "cap_percent": 0.0,
                "band": "insufficient", "note": "质量分缺失，当前新增 0%"}
    if not 0 <= score <= 100:
        raise ValueError("quality score must be within 0-100")
    if score < QUALITY_FLOOR:
        return {"quality_score": score, "cap_percent": 0.0, "band": "fail",
                "note": f"低于 {QUALITY_FLOOR:.0f} 分底线，第 1 步即停，不建仓"}
    for threshold, cap, label in QUALITY_LADDER:
        if score >= threshold:
            band = "pass_downgraded" if score < 60 else f">={threshold:.0f}"
            return {"quality_score": score, "cap_percent": cap,
                    "band": band, "note": label}
    raise AssertionError("unreachable")


def worst_case_preview(
    *,
    position_percent: float,
    entry_price: float,
    deep_value_price: float | None = None,
    bear_price: float | None = None,
) -> dict:
    """给出一个"最坏结果"的心理准备值，而不是一条止损线。

    两个参照：
      - 跌到深度价值线（PR 0.30）意味着还要再跌多少，这一段是可加仓的；
      - 跌到悲观情景价意味着盈利假设本身走坏，这一段是真正的损失预期。
    组合层损失 = 单股跌幅 × 该股仓位。
    """
    out: dict = {"position_percent": position_percent, "entry_price": entry_price}
    for name, price in (("to_deep_value", deep_value_price), ("to_bear_case", bear_price)):
        if price is None:
            out[name] = None
            continue
        drop = (entry_price - price) / entry_price
        out[name] = {
            "price": round(price, 4),
            "stock_drawdown_percent": round(drop * 100.0, 2),
            "portfolio_drag_percent": round(drop * position_percent, 2),
        }
    return out


# ---------------------------------------------------------------------------
# 2026-09-14：建仓阶梯按质量分上限等比缩放，不是截断
# ---------------------------------------------------------------------------

# 原始阶梯是对着 35% 上限设计的，换算成"占上限的比例"后对任何上限都成立：
#   首仓        4%–6%   / 35% = 12%–17%
#   主要加仓累计 10%–15% / 35% = 29%–43%
#   深度价值累计 20%–35% / 35% = 57%–100%
LADDER_FRACTIONS = [
    ("首仓", 0.50, 0.12, 0.17),
    ("主要加仓", 0.40, 0.29, 0.43),
    ("深度价值", 0.30, 0.57, 1.00),
]


def scaled_ladder(cap_percent: float) -> list[dict]:
    """把三档阶梯等比缩放到该股的质量分上限。

    此前的做法是 min(上限, 固定档位额度)，那是**截断**：上限 10% 时
    首仓 4%–6% 原封不动，等于一进场就用掉上限的一半，后面两档几乎没
    有空间，阶梯塌成一档。等比缩放保持"首仓/加仓/深度"的相对节奏不变。
    """
    if cap_percent <= 0:
        return [{"tier": n, "pr_line": pr, "cumulative_percent": None,
                 "status": "blocked_by_quality_gate"}
                for n, pr, _, _ in LADDER_FRACTIONS]
    out = []
    prev_hi = 0.0
    for name, pr, lo, hi in LADDER_FRACTIONS:
        c_lo, c_hi = cap_percent * lo, cap_percent * hi
        out.append({
            "tier": name,
            "pr_line": pr,
            "cumulative_percent": (round(c_lo, 2), round(c_hi, 2)),
            "this_tranche_percent": (round(max(0.0, c_lo - prev_hi), 2), round(c_hi - c_lo + (c_lo - prev_hi if c_lo > prev_hi else 0), 2)) if prev_hi else (round(c_lo, 2), round(c_hi, 2)),
            "share_of_cap": (lo, hi),
        })
        prev_hi = c_hi
    return out


# 第26条（2026-09-18）：前置快筛 —— 第 0 步，两道零成本闸门
# ---------------------------------------------------------------------------

CYCLICAL_TYPES = {"cyclical", "turnaround"}


def prescreen(
    *,
    pb: float | None,
    pe_ttm: float | None,
    roe_ttm_percent: float | None,
    company_type: str,
    is_existing_holding: bool = False,
) -> dict:
    """新建仓路径的第 0 步。任一命中即停，不做质量分／预测／背景调查。

    0a  当前 PB > 8            → 停（全部企业类型适用）
    0b  核验PR = PE_TTM ÷ ROE_TTM > 0.50 → 停（**仅非周期股**）

    0b 的安全性：`执行ROE = min(…, ROE_TTM) ≤ ROE_TTM` ⟹ `决策PR ≥ 核验PR`
    恒成立，所以核验PR 是决策PR 的下界，是单向闸门——只会放行该停的，
    数学上不可能停掉该放的。

    两个禁用条件：
    - **周期股禁用 0b**。低谷期盈利塌陷、PE_TTM 虚高，核验PR 会在它最便宜
      的时候把它杀掉，方向正好反了；周期股本就走 PB 形，PE 形下界关系不成立。
    - `ROE_TTM <= 0` 时 0b 不适用，交回 `decision_pr_status` 既有规则。

    **已有持仓的复查不走第 0 步**：8PB 是买入端禁令、卖出端不看 PB；
    核验PR 同样不产生任何卖出动作。跳过会让持仓失去退出监控。
    """
    if is_existing_holding:
        return {"stop": False, "reason": "existing_holding_full_pipeline",
                "verification_pr": None,
                "note": "已有持仓复查：第 0 步不适用，走完整流程"}
    if pb is None:
        return {"stop": False, "reason": "insufficient_pb", "verification_pr": None,
                "note": "PB 不可得，无法执行 0a，继续但降低置信度"}
    if pb > 8.0:
        return {"stop": True, "reason": "pb_ceiling_breach", "verification_pr": None,
                "note": f"0a：当前PB {pb:.2f} > 8，不建仓"}
    if company_type in CYCLICAL_TYPES:
        return {"stop": False, "reason": "cyclical_0b_excluded", "verification_pr": None,
                "note": "周期股禁用 0b（低谷 PE_TTM 虚高会误杀），仅 0a 生效"}
    if pe_ttm is None or roe_ttm_percent is None or roe_ttm_percent <= 0:
        return {"stop": False, "reason": "verification_pr_not_applicable",
                "verification_pr": None,
                "note": "ROE_TTM ≤ 0 或输入缺失，0b 不适用"}
    vpr = pe_ttm / roe_ttm_percent
    if vpr > 0.50:
        return {"stop": True, "reason": "verification_pr_above_entry",
                "verification_pr": round(vpr, 4),
                "note": f"0b：核验PR {vpr:.4f} > 0.50，决策PR ≥ 核验PR，三档一条也开不了"}
    return {"stop": False, "reason": "prescreen_pass", "verification_pr": round(vpr, 4),
            "note": f"0a PB {pb:.2f} ≤ 8、0b 核验PR {vpr:.4f} ≤ 0.50，进入第 1 步"}


def calibration_checklist(
    *,
    market_coefficient_c: float | None,
    company_type: str,
    payout_percent: float | None,
    dividend_yield_percent: float | None = None,
) -> list[dict]:
    """打印校准项；``c`` 由估值 skill 计算，仓位 skill 只消费。"""
    items = []
    items.append({
        "item": "市场系数 c（第23条：买卖两端同乘）",
        "applies": market_coefficient_c is not None,
        "value": market_coefficient_c,
        "note": (
            "估值交接缺少 c，当前不可执行"
            if market_coefficient_c is None
            else "消费估值交接；判定线=基础线×c，E_market=c"
        ),
    })
    n_excluded = company_type in ("cyclical", "technology", "growth")
    if n_excluded:
        items.append({"item": "股息支付率修正 N", "applies": False, "value": None,
                      "note": f"{company_type} 属排除类型（周期／科技／成长），N 一律不用"})
    elif payout_percent is None:
        items.append({"item": "股息支付率修正 N", "applies": False, "value": None,
                      "note": "分红率缺失，标 insufficient"})
    elif dividend_yield_percent is not None and dividend_yield_percent <= 4.0:
        items.append({"item": "股息支付率修正 N", "applies": False, "value": 1.0,
                      "note": f"股息率 {dividend_yield_percent:.2f}% ≤ 4% 闸门（第24条），"
                              "非红利股，N=1.0 不适用"})
    elif payout_percent <= 0:
        items.append({"item": "股息支付率修正 N", "applies": False, "value": 1.0,
                      "note": "D≤0 → N=1.0（第24条：不是 2.0，无股息说明不在适用范围内）"})
    else:
        n = min(2.0, max(1.0, 50.0 / payout_percent))
        items.append({"item": "股息支付率修正 N", "applies": True, "value": round(n, 4),
                      "note": f"D={payout_percent}% → N=clamp(50/D,1,2)={n:.4f}"
                      + ("（D≥50%，N=1，不产生影响）" if n == 1.0 else "")})
    return items


if __name__ == "__main__":
    main()
