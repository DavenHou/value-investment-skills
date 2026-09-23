#!/usr/bin/env python3
"""Validate a company cache and select the minimum safe refresh mode."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any


FULL = "full_rebuild"
EARNINGS = "earnings_update"
QUICK = "quick_refresh"
FULL_SCOPE = "full"
QUICK_VALUATION_SCOPE = "quick_valuation"
HK_PR_POLICY_VERSION = "hk-dynamic-c-both-sides-v1"
VALUATION_MODEL_VERSION = "ttm-pr-cutoff-locked-v6"
CYCLE_ANCHOR_POLICY_VERSION = "cycle-anchor-conflict-v1"
CACHE_SCHEMA_VERSION = "1.4"
EXIT_POLICY_VERSION = "historical-h-uncapped-v2"
POSITION_SCHEMA_VERSION = "1.7"


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def age_days(value: Any, as_of: date) -> int | None:
    parsed = parse_date(value)
    return None if parsed is None else (as_of - parsed).days


def nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def result(
    mode: str,
    status: str,
    reasons: list[str],
    checks: list[str],
    scope: str = FULL_SCOPE,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "mode": mode,
        "cache_status": status,
        "reasons": reasons,
        "required_checks": checks,
    }


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def close_enough(actual: Any, expected: float, *, price: bool = False) -> bool:
    return is_number(actual) and math.isclose(
        float(actual), expected, rel_tol=1e-4, abs_tol=0.02 if price else 1e-6
    )


def exit_cache_issues(data: dict[str, Any], market: str) -> list[str]:
    handoff = data.get("exit_handoff")
    if not isinstance(handoff, dict):
        return ["exit_handoff_missing"]
    if handoff.get("exit_policy_version") != EXIT_POLICY_VERSION:
        return ["exit_policy_version_changed"]

    issues: list[str] = []
    sample_count = handoff.get("historical_peak_pr_sample_count")
    market_line = 1.0
    if market in {"HK", "HKEX", "H_SHARE", "H-SHARE", "H股"}:
        dividend_yield = nested(data, "valuation_handoff", "dividend_yield_percent")
        tax_percent = nested(data, "valuation_handoff", "dividend_tax_percent")
        cached_c = nested(data, "valuation_handoff", "market_coefficient_c")
        if not all(is_number(value) for value in (dividend_yield, tax_percent, cached_c)):
            issues.append("hk_dynamic_market_coefficient_missing")
            return issues
        expected_c = 0.90 * (1 - float(dividend_yield) * (float(tax_percent) / 100) / 10)
        if expected_c <= 0 or not close_enough(cached_c, expected_c):
            issues.append("hk_dynamic_market_coefficient_mismatch")
            return issues
        market_line = expected_c
    if not close_enough(handoff.get("market_risk_review_pr"), market_line):
        issues.append("exit_anchor_formula_mismatch:E")

    expected: dict[str, float | None] = {"E": market_line, "H": None, "S": None, "M": None}
    if isinstance(sample_count, int) and sample_count >= 2:
        mean = handoff.get("historical_peak_pr_average")
        median = handoff.get("historical_peak_pr_median")
        multiplier = handoff.get("early_exit_multiplier")
        if not is_number(mean) or not is_number(median):
            issues.append("exit_peak_statistics_missing")
        elif multiplier not in {0.8, 0.85}:
            issues.append("exit_early_multiplier_invalid")
        else:
            expected["H"] = min(float(mean), float(median))
            expected["S"] = float(multiplier) * expected["H"]
            expected["M"] = (
                (expected["H"] + market_line) / 2
                if expected["H"] < market_line
                else None
            )
            for key, field in (("H", "historical_h"), ("S", "historical_s")):
                if not close_enough(handoff.get(field), expected[key]):
                    issues.append(f"exit_anchor_formula_mismatch:{key}")
            actual_m = handoff.get("historical_m")
            if expected["M"] is None:
                if actual_m is not None:
                    issues.append("exit_anchor_formula_mismatch:M")
            elif not close_enough(actual_m, expected["M"]):
                issues.append("exit_anchor_formula_mismatch:M")
    elif isinstance(sample_count, int) and sample_count < 2:
        if any(handoff.get(key) is not None for key in ("historical_h", "historical_s", "historical_m")):
            issues.append("exit_anchor_present_with_insufficient_samples")
    else:
        issues.append("exit_peak_sample_count_missing")

    price_map = handoff.get("threshold_prices")
    current_price = nested(data, "price_snapshot", "price")
    current_pr = nested(data, "valuation_handoff", "decision_pr")
    if not isinstance(price_map, dict):
        issues.append("exit_threshold_prices_missing")
    elif is_number(current_price) and is_number(current_pr) and current_pr > 0:
        price_per_pr = float(current_price) / float(current_pr)
        for key, target_pr in expected.items():
            actual_price = price_map.get(key)
            if target_pr is None:
                if actual_price is not None:
                    issues.append(f"exit_threshold_price_mismatch:{key}")
            elif not close_enough(actual_price, price_per_pr * target_pr, price=True):
                issues.append(f"exit_threshold_price_mismatch:{key}")
    else:
        issues.append("exit_threshold_price_basis_missing")
    return issues


def position_cache_issues(data: dict[str, Any]) -> list[str]:
    handoff = data.get("position_handoff")
    if not isinstance(handoff, dict):
        return ["position_handoff_missing"]
    if handoff.get("schema_version") != POSITION_SCHEMA_VERSION:
        return ["position_schema_version_changed"]

    required = [
        "executable_percent_now",
        "conditional_initial_percent",
        "valuation_supported_cumulative_percent",
        "portfolio_risk_budget_status",
        "max_completed_position_drawdown_percent",
        "completed_ladder_drawdown_status",
        "stock_count_assessment",
        "unallocated_capital_policy",
    ]
    missing = [key for key in required if handoff.get(key) is None]
    if missing:
        return ["position_fields_missing:" + ",".join(missing)]

    issues: list[str] = []
    executable = handoff.get("executable_percent_now")
    conditional = handoff.get("conditional_initial_percent")
    supported = handoff.get("valuation_supported_cumulative_percent")
    if not all(is_number(value) for value in (executable, conditional, supported)):
        issues.append("position_percent_fields_invalid")
    elif executable > conditional or executable > supported:
        issues.append("executable_position_exceeds_conditional_or_valuation_support")
    if handoff.get("portfolio_risk_budget_status") not in {
        "selected",
        "not_selected_sensitivity_only",
    }:
        issues.append("portfolio_risk_budget_status_invalid")
    if not close_enough(handoff.get("max_completed_position_drawdown_percent"), 50.0):
        issues.append("completed_position_drawdown_limit_changed")
    if handoff.get("unallocated_capital_policy") != "hold_cash_do_not_fill_to_minimum":
        issues.append("unallocated_capital_policy_changed")
    return issues


def select_mode(args: argparse.Namespace) -> dict[str, Any]:
    scope = getattr(args, "scope", FULL_SCOPE)
    quick_valuation = scope == QUICK_VALUATION_SCOPE
    cache_path = Path(args.cache)
    checks = ["official_disclosure_change_check"]
    if quick_valuation:
        checks.extend(
            [
                "refresh_current_price_and_fx",
                "refresh_pure_cash_coverage",
                "validate_three_year_forecast_and_normalization",
            ]
        )
    else:
        checks.append("refresh_current_price_and_peers")

    if not cache_path.exists():
        return result(FULL, "miss", ["cache_missing"], checks, scope)

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return result(
            FULL,
            "invalid",
            [f"cache_unreadable:{type(exc).__name__}"],
            checks,
            scope,
        )

    if not isinstance(data, dict):
        return result(FULL, "invalid", ["cache_root_not_object"], checks, scope)

    reasons: list[str] = []
    if args.identity_change:
        reasons.append("identity_or_share_rights_changed")
    if args.major_event:
        reasons.append("major_governance_audit_or_business_event")

    required_sections = ["company_identity", "forecast_handoff", "valuation_handoff"]
    if not quick_valuation:
        required_sections.append("research_handoff")
    missing_sections = [key for key in required_sections if not isinstance(data.get(key), dict)]
    if missing_sections:
        reasons.append("missing_sections:" + ",".join(missing_sections))

    if not quick_valuation:
        research_status = nested(data, "research_handoff", "status")
        score = nested(data, "research_handoff", "score")
        coverage = nested(data, "research_handoff", "evidence_coverage_percent")
        research_cutoff = parse_date(nested(data, "research_handoff", "evidence_cutoff"))
        research_age = age_days(
            nested(data, "research_handoff", "evidence_cutoff"), args.as_of
        )

        if research_status != "pass":
            reasons.append("research_not_pass")
        if not isinstance(score, (int, float)):
            reasons.append("formal_score_missing")
        if not isinstance(coverage, (int, float)) or coverage < 80:
            reasons.append("research_coverage_below_80")
        if research_age is None:
            reasons.append("research_date_missing_or_invalid")
        elif research_cutoff and research_cutoff > args.as_of:
            reasons.append("research_evidence_after_as_of")
        elif research_age > 370:
            reasons.append("research_older_than_370_days")

    if reasons:
        return result(FULL, "invalid", reasons, checks, scope)

    forecast_status = nested(data, "forecast_handoff", "status")
    valuation_status = nested(data, "valuation_handoff", "status")
    cached_filing = nested(data, "forecast_handoff", "latest_filing_id")
    forecast_cutoff = parse_date(nested(data, "forecast_handoff", "evidence_cutoff"))
    forecast_age = age_days(
        nested(data, "forecast_handoff", "evidence_cutoff"), args.as_of
    )
    earnings_reasons: list[str] = []

    if data.get("schema_version") != CACHE_SCHEMA_VERSION:
        earnings_reasons.append("cache_schema_version_changed")

    if forecast_status != "usable":
        earnings_reasons.append("forecast_not_usable")
    if forecast_cutoff is None:
        earnings_reasons.append("forecast_date_missing_or_invalid")
    elif forecast_cutoff > args.as_of:
        earnings_reasons.append("forecast_evidence_after_as_of")
    forecast_required = [
        "base_eps",
        "bear_eps",
        "neutral_roe_percent",
        "bull_roe_percent",
        "bear_roe_percent",
        "neutral_roa_percent",
        "bull_roa_percent",
        "bear_roa_percent",
    ]
    missing_forecast_fields = [
        key for key in forecast_required if nested(data, "forecast_handoff", key) is None
    ]
    if missing_forecast_fields:
        earnings_reasons.append(
            "forecast_fields_missing:" + ",".join(missing_forecast_fields)
        )
    if valuation_status != "valid":
        earnings_reasons.append("valuation_not_valid")
    valuation_required = [
        "ttm_period_end",
        "pe_ttm",
        "roe_ttm_percent",
        "pr_ttm",
        "decision_roe_percent",
        "decision_pr",
        "forecast_tier",
        "major_earnings_decline_status",
        "calculation_basis_id",
        "price_bands",
    ]
    missing_valuation_fields = [
        key for key in valuation_required if nested(data, "valuation_handoff", key) is None
    ]
    if missing_valuation_fields:
        earnings_reasons.append(
            "valuation_fields_missing:" + ",".join(missing_valuation_fields)
        )
    price_date = parse_date(nested(data, "price_snapshot", "price_date"))
    if price_date is None:
        earnings_reasons.append("price_date_missing_or_invalid")
    elif price_date > args.as_of:
        earnings_reasons.append("price_date_after_as_of")
    ttm_period_end = parse_date(nested(data, "valuation_handoff", "ttm_period_end"))
    if ttm_period_end and ttm_period_end > args.as_of:
        earnings_reasons.append("valuation_period_after_as_of")
    valuation_model_version = nested(data, "valuation_handoff", "valuation_model_version")
    if valuation_model_version != VALUATION_MODEL_VERSION:
        earnings_reasons.append("valuation_model_version_changed")
    company_type = nested(data, "valuation_handoff", "company_type")
    if company_type != "cyclical" and nested(data, "valuation_handoff", "ttm_diluted_eps") is None:
        earnings_reasons.append("valuation_fields_missing:ttm_diluted_eps")
    if company_type == "cyclical":
        if nested(data, "valuation_handoff", "cycle_anchor_policy_version") != CYCLE_ANCHOR_POLICY_VERSION:
            earnings_reasons.append("cycle_anchor_policy_version_changed")
        cyclical_required = [
            "pb",
            "current_run_rate_roe_percent",
            "neutral_roe_percent",
            "bear_roe_percent",
        ]
        missing_cyclical_fields = [
            key
            for key in cyclical_required
            if nested(data, "valuation_handoff", key) is None
        ]
        if missing_cyclical_fields:
            earnings_reasons.append(
                "cycle_anchor_fields_missing:" + ",".join(missing_cyclical_fields)
            )
        if nested(data, "valuation_handoff", "cycle_anchor_conflict_status") not in {
            "aligned",
            "material_gap",
            "regime_split",
        }:
            earnings_reasons.append("cycle_anchor_conflict_missing_or_insufficient")
    stable_three_year_status = nested(
        data, "valuation_handoff", "stable_three_year_status"
    )
    if company_type == "stable" and stable_three_year_status not in {
        "strict_stable",
        "relaxed_stable",
    }:
        earnings_reasons.append("stable_three_year_classification_missing_or_unusable")
    if (
        company_type == "stable"
        and stable_three_year_status == "relaxed_stable"
        and not quick_valuation
    ):
        if nested(data, "valuation_handoff", "candidate_scarcity_confirmed") is not True:
            earnings_reasons.append("relaxed_stability_candidate_scarcity_not_confirmed")
        if nested(data, "valuation_handoff", "relaxed_position_cap_percent") != 15:
            earnings_reasons.append("relaxed_stability_position_cap_missing_or_changed")
    extreme_roe_review_required = nested(
        data, "valuation_handoff", "extreme_roe_review_required"
    )
    roe_reliability = nested(data, "valuation_handoff", "roe_reliability")
    if not isinstance(extreme_roe_review_required, bool):
        earnings_reasons.append("extreme_roe_review_status_missing")
    elif extreme_roe_review_required and roe_reliability not in {
        "organic_high_return",
        "usable_with_caution",
    }:
        earnings_reasons.append("extreme_roe_review_unresolved_or_distorted")
    elif not extreme_roe_review_required and roe_reliability != "not_triggered":
        earnings_reasons.append("roe_reliability_status_inconsistent")
    if args.latest_filing_id and args.latest_filing_id != cached_filing:
        earnings_reasons.append("new_filing_detected")
    if args.earnings_event:
        earnings_reasons.append("earnings_or_guidance_event")
    market = str(nested(data, "company_identity", "market") or "").upper()
    exit_cutoff = parse_date(nested(data, "exit_handoff", "evidence_cutoff"))
    if exit_cutoff is None:
        earnings_reasons.append("exit_date_missing_or_invalid")
    elif exit_cutoff > args.as_of:
        earnings_reasons.append("exit_evidence_after_as_of")
    earnings_reasons.extend(exit_cache_issues(data, market))
    if not quick_valuation:
        earnings_reasons.extend(position_cache_issues(data))
    if market in {"HK", "HKEX", "H_SHARE", "H-SHARE", "H股"}:
        policy_version = nested(data, "valuation_handoff", "market_pr_policy_version")
        if policy_version != HK_PR_POLICY_VERSION:
            earnings_reasons.append("hk_market_pr_policy_changed")

    if earnings_reasons:
        return result(EARNINGS, "partial", earnings_reasons, checks, scope)

    quick_reasons = [
        "formal_forecast_valuation_exit_handoffs_reusable"
        if quick_valuation
        else "formal_handoffs_reusable"
    ]
    if forecast_age is None or forecast_age > 130:
        checks.append("resolve_forecast_age_with_official_filing_id")
        quick_reasons.append("forecast_age_requires_explicit_disclosure_check")
    if abs(args.price_move_percent) >= 8:
        quick_reasons.append("price_move_revalue_threshold_crossed")
    if args.peer_trigger and not quick_valuation:
        quick_reasons.append("peer_timing_triggered")

    return result(QUICK, "hit", quick_reasons, checks, scope)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, help="Path to the company cache JSON file")
    parser.add_argument(
        "--scope",
        choices=(FULL_SCOPE, QUICK_VALUATION_SCOPE),
        default=FULL_SCOPE,
        help="Requested module scope; refresh mode is selected independently",
    )
    parser.add_argument("--as-of", type=lambda value: datetime.strptime(value, "%Y-%m-%d").date(), default=date.today())
    parser.add_argument("--latest-filing-id", help="Latest official filing identifier discovered in the change check")
    parser.add_argument("--price-move-percent", type=float, default=0.0)
    parser.add_argument("--major-event", action="store_true")
    parser.add_argument("--identity-change", action="store_true")
    parser.add_argument("--earnings-event", action="store_true")
    parser.add_argument("--peer-trigger", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = select_mode(args)
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
