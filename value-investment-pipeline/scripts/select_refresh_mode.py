#!/usr/bin/env python3
"""Validate a company cache and select the minimum safe refresh mode."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


FULL = "full_rebuild"
EARNINGS = "earnings_update"
QUICK = "quick_refresh"
HK_PR_POLICY_VERSION = "hk-pr-threshold-0.80-v1"
VALUATION_MODEL_VERSION = "ttm-pr-dupont-v4"
CACHE_SCHEMA_VERSION = "1.2"


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


def result(mode: str, status: str, reasons: list[str], checks: list[str]) -> dict[str, Any]:
    return {
        "mode": mode,
        "cache_status": status,
        "reasons": reasons,
        "required_checks": checks,
    }


def select_mode(args: argparse.Namespace) -> dict[str, Any]:
    cache_path = Path(args.cache)
    checks = ["official_disclosure_change_check", "refresh_current_price_and_peers"]

    if not cache_path.exists():
        return result(FULL, "miss", ["cache_missing"], checks)

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return result(FULL, "invalid", [f"cache_unreadable:{type(exc).__name__}"], checks)

    if not isinstance(data, dict):
        return result(FULL, "invalid", ["cache_root_not_object"], checks)

    reasons: list[str] = []
    if args.identity_change:
        reasons.append("identity_or_share_rights_changed")
    if args.major_event:
        reasons.append("major_governance_audit_or_business_event")

    required_sections = ["company_identity", "research_handoff", "forecast_handoff", "valuation_handoff"]
    missing_sections = [key for key in required_sections if not isinstance(data.get(key), dict)]
    if missing_sections:
        reasons.append("missing_sections:" + ",".join(missing_sections))

    research_status = nested(data, "research_handoff", "status")
    score = nested(data, "research_handoff", "score")
    coverage = nested(data, "research_handoff", "evidence_coverage_percent")
    research_age = age_days(nested(data, "research_handoff", "evidence_cutoff"), args.as_of)

    if research_status != "pass":
        reasons.append("research_not_pass")
    if not isinstance(score, (int, float)):
        reasons.append("formal_score_missing")
    if not isinstance(coverage, (int, float)) or coverage < 80:
        reasons.append("research_coverage_below_80")
    if research_age is None:
        reasons.append("research_date_missing_or_invalid")
    elif research_age > 370:
        reasons.append("research_older_than_370_days")

    if reasons:
        return result(FULL, "invalid", reasons, checks)

    forecast_status = nested(data, "forecast_handoff", "status")
    valuation_status = nested(data, "valuation_handoff", "status")
    cached_filing = nested(data, "forecast_handoff", "latest_filing_id")
    forecast_age = age_days(nested(data, "forecast_handoff", "evidence_cutoff"), args.as_of)
    earnings_reasons: list[str] = []

    if data.get("schema_version") != CACHE_SCHEMA_VERSION:
        earnings_reasons.append("cache_schema_version_changed")

    if forecast_status != "usable":
        earnings_reasons.append("forecast_not_usable")
    forecast_required = [
        "base_eps",
        "bear_eps",
        "neutral_roe_percent",
        "bear_roe_percent",
        "neutral_roa_percent",
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
    valuation_required = ["pe_ttm", "roe_ttm_percent", "pr_ttm", "price_bands"]
    missing_valuation_fields = [
        key for key in valuation_required if nested(data, "valuation_handoff", key) is None
    ]
    if missing_valuation_fields:
        earnings_reasons.append(
            "valuation_fields_missing:" + ",".join(missing_valuation_fields)
        )
    valuation_model_version = nested(data, "valuation_handoff", "valuation_model_version")
    if valuation_model_version != VALUATION_MODEL_VERSION:
        earnings_reasons.append("valuation_model_version_changed")
    company_type = nested(data, "valuation_handoff", "company_type")
    stable_three_year_status = nested(
        data, "valuation_handoff", "stable_three_year_status"
    )
    if company_type == "stable" and stable_three_year_status not in {
        "strict_stable",
        "relaxed_stable",
    }:
        earnings_reasons.append("stable_three_year_classification_missing_or_unusable")
    if company_type == "stable" and stable_three_year_status == "relaxed_stable":
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
    if market in {"HK", "HKEX", "H_SHARE", "H-SHARE", "H股"}:
        policy_version = nested(data, "valuation_handoff", "market_pr_policy_version")
        if policy_version != HK_PR_POLICY_VERSION:
            earnings_reasons.append("hk_market_pr_policy_changed")

    if earnings_reasons:
        return result(EARNINGS, "partial", earnings_reasons, checks)

    quick_reasons = ["formal_handoffs_reusable"]
    if forecast_age is None or forecast_age > 130:
        checks.append("resolve_forecast_age_with_official_filing_id")
        quick_reasons.append("forecast_age_requires_explicit_disclosure_check")
    if abs(args.price_move_percent) >= 8:
        quick_reasons.append("price_move_revalue_threshold_crossed")
    if args.peer_trigger:
        quick_reasons.append("peer_timing_triggered")

    return result(QUICK, "hit", quick_reasons, checks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, help="Path to the company cache JSON file")
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
