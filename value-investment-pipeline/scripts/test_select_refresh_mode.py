#!/usr/bin/env python3

import argparse
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from select_refresh_mode import (
    CACHE_SCHEMA_VERSION,
    EARNINGS,
    FULL,
    HK_PR_POLICY_VERSION,
    QUICK,
    VALUATION_MODEL_VERSION,
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
            "bear_roe_percent": 14.0,
            "neutral_roa_percent": 9.0,
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
            "pe_ttm": 15.0,
            "roe_ttm_percent": 20.0,
            "pr_ttm": 0.75,
            "price_bands": {"initial": [10.0, 12.0]},
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

    def test_missing_required_valuation_field_requires_update(self):
        cache = valid_cache()
        cache["valuation_handoff"]["price_bands"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_fields_missing:price_bands", output["reasons"])

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
        cache["valuation_handoff"]["valuation_model_version"] = "ttm-pr-dupont-v3"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text(json.dumps(cache), encoding="utf-8")
            output = select_mode(args(str(path)))
        self.assertEqual(output["mode"], EARNINGS)
        self.assertIn("valuation_model_version_changed", output["reasons"])

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
