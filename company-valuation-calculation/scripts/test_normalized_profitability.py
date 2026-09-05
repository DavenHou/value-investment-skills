#!/usr/bin/env python3

import unittest

from calculate_normalized_profitability import calculate


class NormalizedProfitabilityTests(unittest.TestCase):
    def stable_inputs(self) -> dict:
        return {
            "company_type": "stable",
            "historical_roe": [18.0, 20.0, 22.0],
            "forecast_base_roe": [20.0, 21.0, 22.0],
            "forecast_bear_roe": [17.0, 18.0, 19.0],
            "historical_roa": [9.0, 10.0, 11.0],
            "forecast_base_roa": [10.0, 10.5, 11.0],
            "forecast_bear_roa": [8.0, 9.0, 9.5],
            "current_ttm_roe": 21.0,
            "current_ttm_roa": 10.5,
            "stable_years_comparable": "confirmed",
        }

    def test_stable_neutral_anchor_is_latest_three_year_equal_mean(self):
        output = calculate(**self.stable_inputs())
        self.assertEqual(
            output["historical_selection"]["neutral_anchor_method"],
            "latest_three_comparable_full_years_equal_weight",
        )
        self.assertAlmostEqual(output["roe_percent"]["historical_neutral_anchor"], 20.0)
        self.assertTrue(output["stable_three_year_stability"]["neutral_anchor_usable"])
        self.assertAlmostEqual(output["roe_percent"]["normalized_neutral"], 20.28)

    def test_stable_gate_fails_when_three_year_roe_is_not_stable(self):
        inputs = self.stable_inputs()
        inputs["historical_roe"] = [10.0, 20.0, 30.0]
        output = calculate(**inputs)
        self.assertEqual(
            output["stable_three_year_stability"]["quantitative_status"], "unstable"
        )
        self.assertFalse(output["stable_three_year_stability"]["neutral_anchor_usable"])

    def test_candidate_scarcity_allows_controlled_stability_relaxation(self):
        inputs = self.stable_inputs()
        inputs.update(
            {
                "historical_roe": [11.0, 20.0, 29.0],
                "stability_policy": "controlled_relaxation",
                "strict_candidate_count": 4,
                "minimum_candidate_count": 6,
            }
        )
        output = calculate(**inputs)
        stability = output["stable_three_year_stability"]
        self.assertEqual(stability["stability_tier"], "relaxed_stable")
        self.assertTrue(stability["neutral_anchor_usable"])
        self.assertTrue(output["roe_pr_executable"])
        self.assertIn("cumulative_cap_15_percent", stability["position_treatment"])

    def test_relaxation_is_not_allowed_when_strict_pool_is_large_enough(self):
        inputs = self.stable_inputs()
        inputs.update(
            {
                "historical_roe": [11.0, 20.0, 29.0],
                "stability_policy": "controlled_relaxation",
                "strict_candidate_count": 6,
                "minimum_candidate_count": 6,
            }
        )
        output = calculate(**inputs)
        self.assertEqual(
            output["stable_three_year_stability"]["stability_tier"], "unstable"
        )
        self.assertFalse(output["roe_pr_executable"])

    def test_high_roe_buyback_distortion_makes_pr_diagnostic_only(self):
        inputs = self.stable_inputs()
        inputs.update(
            {
                "historical_roe": [90.0, 100.0, 110.0],
                "current_ttm_roe": 115.0,
                "high_roe_review_status": "buyback_or_leverage_distorted",
            }
        )
        output = calculate(**inputs)
        self.assertTrue(output["high_roe_review"]["triggered"])
        self.assertTrue(output["high_roe_review"]["review_resolved"])
        self.assertEqual(output["high_roe_review"]["pr_roe_role"], "diagnostic_only")
        self.assertFalse(output["roe_pr_executable"])
        self.assertTrue(
            output["high_roe_review"]["roa_must_not_be_substituted_directly_into_pr_formula"]
        )

    def test_high_roe_pending_review_stays_diagnostic(self):
        inputs = self.stable_inputs()
        inputs["current_ttm_roe"] = 45.0
        output = calculate(**inputs)
        self.assertFalse(output["high_roe_review"]["review_resolved"])
        self.assertEqual(output["high_roe_review"]["pr_roe_role"], "diagnostic_only")


if __name__ == "__main__":
    unittest.main()
