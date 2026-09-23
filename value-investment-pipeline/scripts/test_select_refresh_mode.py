#!/usr/bin/env python3

import argparse
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from select_refresh_mode import (
    CACHE_SCHEMA_VERSION,
    CYCLE_ANCHOR_POLICY_VERSION,
    EARNINGS,
    EXIT_POLICY_VERSION,
    FULL,
    FULL_SCOPE,
    HK_PR_POLICY_VERSION,
    QUICK,
    QUICK_VALUATION_SCOPE,
    VALUATION_MODEL_VERSION,
    POSITION_SCHEMA_VERSION,
    select_mode,
)


def valid_cache() -> dict:
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "company_identity": {
            "legal_name": "Example Co",
            "security": "000001",
            "market": "SZSE",
            "currency": "CNY",
            "share_class": "A",
            "identity_checked_at": "2026-08-01",
        },
        "research_handoff": {
            "status": "pass",
            "score": 75.2,
            "evidence_coverage_percent": 90,
            "evidence_cutoff": "2026-04-30",
        },
        "forecast_handoff": {
            "status": "usable",
            "latest_filing_id": "2026-H1",
            "evidence_cutoff": "2026-08-20",
            "base_eps": 3.20,
            "bear_eps": 2.70,
            "neutral_roe_percent": 18.0,
            "bull_roe_percent": 20.0,
            "bear_roe_percent": 14.0,
            "neutral_roa_percent": 9.0,
            "bull_roa_percent": 10.0,
            "bear_roa_percent": 7.0,
        },
        "valuation_handoff": {
            "status": "valid",
            "calculated_at": "2026-08-20",
            "valuation_model_version": VALUATION_MODEL_VERSION,
            "company_type": "stable",
            "stable_three_year_status": "strict_stable",
            "extreme_roe_review_required": False,
            "roe_reliability": "not_triggered",
            "ttm_period_end": "2026-06-30",
            "ttm_diluted_eps": 2 / 3,
            "pe_ttm": 15.0,
            "roe_ttm_percent": 20.0,
            "pr_ttm": 0.75,
            "decision_roe_percent": 20.0,
            "decision_pr": 0.75,
            "forecast_tier": "bear",
            "major_earnings_decline_status": "未触发",
            "calculation_basis_id": "2026-06-30|actual-ttm|stable-v5",
            "price_bands": {"initial": [10.0, 12.0]},
        },
        "exit_handoff": {
            "exit_policy_version": EXIT_POLICY_VERSION,
            "evidence_cutoff": "2026-08-20",
            "historical_peak_pr_sample_count": 3,
            "historical_peak_pr_average": 1.10,
            "historical_peak_pr_median": 1.05,
            "early_exit_multiplier": 0.85,
            "historical_h": 1.05,
            "historical_s": 0.8925,
            "historical_m": None,
            "market_risk_review_pr": 1.0,
            "threshold_prices": {
                "S": 11.9,
                "H": 14.0,
                "M": None,
                "E": 13.33,
            },
        },
        "price_snapshot": {
            "price": 10.0,
            "price_date": "2026-08-31",
        },
        "position_handoff": {
            "schema_version": POSITION_SCHEMA_VERSION,
            "executable_percent_now": 4.0,
            "conditional_initial_percent": 4.0,
            "valuation_supported_cumulative_percent": 20.0,
            "portfolio_risk_budget_status": "not_selected_sensitivity_only",
            "max_completed_position_drawdown_percent": 50.0,
            "completed_ladder_drawdown_status": "pending_exact_ladder",
            "stock_count_assessment": "assumed_within_policy_by_user",
            "unallocated_capital_policy": "hold_cash_do_not_fill_to_minimum",
        },
    }


def args(cache: str, **overrides) -> argparse.Namespace:
    values = {
        "cache": cache,
        "as_of": date(2026, 9, 1),
        "latest_filing_id": "2026-H1",
        "price_move_percent": 0.0,
        "major_event": False,
        "identity_change": False,
        "earnings_event": False,
        "peer_trigger": False,
        "scope": FULL_SCOPE,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class SelectRefreshModeTests(unittest.TestCase):
    def test_missing_cache_requires_full_rebuild(self):
        output = select_mode(args("/path/that/does/not/exist.json"))
        self.assertEqual(output["mode"], FULL)
        self.assertEqual(output["cache_status"], "miss")

    def test_valid_cache_uses_quick_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(valid_cache()), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)
        self.assertEqual(output["cache_status"], "hit")
        self.assertEqual(output["scope"], FULL_SCOPE)

    def test_quick_valuation_skips_only_research_peers_and_position(self):
        cache = valid_cache()
        cache.pop("research_handoff")
        cache.pop("position_handoff")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(
                args(
                    str(path),
                    scope=QUICK_VALUATION_SCOPE,
                    peer_trigger=True,
                )
            )
        self.assertEqual(output["mode"], QUICK)
        self.assertEqual(output["scope"], QUICK_VALUATION_SCOPE)
        self.assertNotIn("peer_timing_triggered", output["reasons"])
        self.assertNotIn("refresh_current_price_and_peers", output["required_checks"])
        self.assertIn("refresh_pure_cash_coverage", output["required_checks"])
        self.assertIn(
            "validate_three_year_forecast_and_normalization",
            output["required_checks"],
        )

    def test_quick_valuation_still_requires_forecast_valuation_and_exit(self):
        cache = valid_cache()
        cache["forecast_handoff"]["bear_eps"] = None
        cache["valuation_handoff"]["decision_pr"] = None
        cache["exit_handoff"].pop("exit_policy_version")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(
                args(str(path), scope=QUICK_VALUATION_SCOPE)
            )
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("forecast_fields_missing:bear_eps", output["reasons"])
        self.assertIn("valuation_fields_missing:decision_pr", output["reasons"])
        self.assertIn("exit_policy_version_changed", output["reasons"])

    def test_historical_quick_valuation_rejects_future_evidence(self):
        cache = valid_cache()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(
                args(
                    str(path),
                    scope=QUICK_VALUATION_SCOPE,
                    as_of=date(2022, 10, 31),
                )
            )
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("forecast_evidence_after_as_of", output["reasons"])
        self.assertIn("price_date_after_as_of", output["reasons"])
        self.assertIn("valuation_period_after_as_of", output["reasons"])
        self.assertIn("exit_evidence_after_as_of", output["reasons"])

    def test_new_filing_uses_earnings_update(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(valid_cache()), encoding="utf-8")
            output = select_mode(args(str(path), latest_filing_id="2026-Q3"))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("new_filing_detected", output["reasons"])

    def test_missing_valuation_version_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"].pop("valuation_model_version")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_model_version_changed", output["reasons"])

    def test_missing_required_forecast_field_requires_update(self):
        cache = valid_cache()
        cache["forecast_handoff"]["bear_eps"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("forecast_fields_missing:bear_eps", output["reasons"])

    def test_missing_bull_or_decline_handoff_requires_update(self):
        for section, field, reason in (
            ("forecast_handoff", "bull_roe_percent", "forecast_fields_missing:bull_roe_percent"),
            ("valuation_handoff", "major_earnings_decline_status",
             "valuation_fields_missing:major_earnings_decline_status"),
        ):
            with self.subTest(field=field):
                cache = valid_cache()
                cache[section][field] = None
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "cache.json"
                    path.write_text(json.dumps(cache), encoding="utf-8")
                    output = select_mode(args(str(path)))
                self.assertEqual(output["mode"], EARNINGS)
                self.assertIn(reason, output["reasons"])

    def test_missing_required_valuation_field_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["price_bands"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_fields_missing:price_bands", output["reasons"])

    def test_current_cyclical_anchor_policy_uses_quick_refresh(self):
        cache = valid_cache()
        cache["valuation_handoff"].update(
            {
                "company_type": "cyclical",
                "cycle_anchor_policy_version": CYCLE_ANCHOR_POLICY_VERSION,
                "cycle_anchor_conflict_status": "material_gap",
                "pb": 1.14,
                "current_run_rate_roe_percent": 10.8,
                "neutral_roe_percent": 14.59,
                "bear_roe_percent": 10.8,
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)

    def test_legacy_cyclical_cache_requires_anchor_recalculation(self):
        cache = valid_cache()
        cache["valuation_handoff"]["company_type"] = "cyclical"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("cycle_anchor_policy_version_changed", output["reasons"])
        self.assertIn(
            "cycle_anchor_fields_missing:pb,current_run_rate_roe_percent,neutral_roe_percent,bear_roe_percent",
            output["reasons"],
        )
        self.assertIn("cycle_anchor_conflict_missing_or_insufficient", output["reasons"])

    def test_historical_anchor_can_exceed_market_risk_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(valid_cache()), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)

    def test_old_h_capped_at_market_line_requires_update(self):
        cache = valid_cache()
        cache["exit_handoff"]["historical_h"] = 1.0
        cache["exit_handoff"]["historical_s"] = 0.85
        cache["exit_handoff"]["threshold_prices"] = {
            "S": 11.33,
            "H": 13.33,
            "M": None,
            "E": 13.33,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("exit_anchor_formula_mismatch:H", output["reasons"])

    def test_stale_exit_price_map_requires_update(self):
        cache = valid_cache()
        cache["exit_handoff"]["threshold_prices"]["H"] = 12.0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("exit_threshold_price_mismatch:H", output["reasons"])

    def test_exit_price_map_uses_decision_pr_not_verification_pr(self):
        cache = valid_cache()
        cache["valuation_handoff"]["pr_ttm"] = 0.60
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)

    def test_missing_exit_policy_version_requires_update(self):
        cache = valid_cache()
        cache["exit_handoff"].pop("exit_policy_version")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("exit_policy_version_changed", output["reasons"])

    def test_legacy_ambiguous_position_handoff_requires_update(self):
        cache = valid_cache()
        cache["position_handoff"] = {
            "status": "conditional",
            "recommended_percent": 4.0,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("position_schema_version_changed", output["reasons"])

    def test_old_cache_schema_requires_update(self):
        cache = valid_cache()
        cache["schema_version"] = "1.1"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("cache_schema_version_changed", output["reasons"])

    def test_non_current_model_version_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["valuation_model_version"] = "ttm-pr-cutoff-locked-v5"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_model_version_changed", output["reasons"])

    def test_missing_calculation_basis_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["calculation_basis_id"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_fields_missing:calculation_basis_id", output["reasons"])

    def test_hk_cache_without_current_pr_policy_requires_valuation_update(self):
        cache = valid_cache()
        cache["company_identity"]["market"] = "HKEX"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("hk_market_pr_policy_changed", output["reasons"])

    def test_hk_cache_with_current_pr_policy_uses_quick_refresh(self):
        cache = valid_cache()
        cache["company_identity"]["market"] = "HKEX"
        cache["valuation_handoff"]["market_pr_policy_version"] = HK_PR_POLICY_VERSION
        cache["valuation_handoff"]["dividend_yield_percent"] = 8.4
        cache["valuation_handoff"]["dividend_tax_percent"] = 20.0
        cache["valuation_handoff"]["market_coefficient_c"] = 0.7488
        cache["exit_handoff"]["market_risk_review_pr"] = 0.7488
        cache["exit_handoff"]["threshold_prices"]["E"] = 9.98
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)

    def test_unresolved_extreme_roe_requires_valuation_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["extreme_roe_review_required"] = True
        cache["valuation_handoff"]["roe_reliability"] = "insufficient"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("extreme_roe_review_unresolved_or_distorted", output["reasons"])

    def test_documented_relaxed_stable_cache_can_use_quick_refresh(self):
        cache = valid_cache()
        cache["valuation_handoff"]["stable_three_year_status"] = "relaxed_stable"
        cache["valuation_handoff"]["candidate_scarcity_confirmed"] = True
        cache["valuation_handoff"]["relaxed_position_cap_percent"] = 15
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], QUICK)

    def test_undocumented_relaxed_stable_cache_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["stable_three_year_status"] = "relaxed_stable"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn(
            "relaxed_stability_candidate_scarcity_not_confirmed", output["reasons"]
        )

    def test_quick_valuation_ignores_relaxed_stability_position_conditions(self):
        cache = valid_cache()
        cache["valuation_handoff"]["stable_three_year_status"] = "relaxed_stable"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(
                args(str(path), scope=QUICK_VALUATION_SCOPE)
            )
        self.assertEqual(output["mode"], QUICK)

    def test_major_event_requires_full_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(valid_cache()), encoding="utf-8")
            output = select_mode(args(str(path), major_event=True))
        self.assertEqual(output["mode"], FULL)

    def test_stale_research_requires_full_rebuild(self):
        cache = valid_cache()
        cache["research_handoff"]["evidence_cutoff"] = "2025-01-01"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], FULL)
        self.assertIn("research_older_than_370_days", output["reasons"])


if __name__ == "__main__":
    unittest.main()
