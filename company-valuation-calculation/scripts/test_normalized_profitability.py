#!/usr/bin/env python3

import unittest

from calculate_normalized_profitability import calculate


class NormalizedProfitabilityTests(unittest.TestCase):
    def test_cyclical_five_year_low_drives_formal_bear_roe_and_matching_roa(self):
        result = calculate(
            company_type="cyclical",
            historical_roe=[1, 2, 3, 4, 5, 11, 7, 4, 9, 15],
            historical_roa=[0.5, 1, 1.5, 2, 2.5, 6, 4, 2, 5, 8],
            forecast_bear_roe=[6, 7, 8],
            forecast_bear_roa=[3, 3.5, 4],
            historical_phases=["trough", "trough", "recovery", "recovery", "boom",
                               "boom", "downturn", "downturn", "recovery", "boom"],
        )
        self.assertEqual(result["historical_selection"]["cycle_five_year_low_index_oldest_is_1"], 8)
        self.assertAlmostEqual(result["roe_percent"]["historical_anchor_used"], 4.0)
        self.assertAlmostEqual(result["roe_percent"]["normalized_bear"], 4.8)
        self.assertAlmostEqual(result["roe_percent"]["cyclical_60_40_sensitivity_non_executable"], 5.0666666667)
        self.assertAlmostEqual(result["roa_percent"]["historical_anchor_used"], 2.0)
        self.assertTrue(result["roe_pr_executable"])

    def test_cyclical_nonpositive_five_year_low_blocks_execution(self):
        result = calculate(company_type="cyclical", historical_roe=[4, 6, 5, 7, -1],
                           forecast_bear_roe=[6, 7, 8])
        self.assertFalse(result["roe_pr_executable"])

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

    def test_stable_neutral_uses_conservative_history_anchor_fifty_fifty(self):
        output = calculate(**self.stable_inputs())
        self.assertEqual(
            output["historical_selection"]["neutral_anchor_method"],
            "historical_conservative_anchor_shared_with_bear",
        )
        self.assertAlmostEqual(output["roe_percent"]["historical_neutral_anchor"], 20.0)
        self.assertAlmostEqual(
            output["roe_percent"]["historical_anchor_used_for_normalized_neutral"],
            19.142857142857142,
        )
        self.assertTrue(output["stable_three_year_stability"]["neutral_anchor_usable"])
        self.assertAlmostEqual(output["weights"]["history_share"], 0.50)
        self.assertAlmostEqual(output["weights"]["forecast_share"], 0.50)
        self.assertAlmostEqual(output["roe_percent"]["normalized_neutral"], 19.97142857142857)
        self.assertAlmostEqual(output["roe_percent"]["normalized_bear"], 18.47142857142857)

    def test_stable_bull_uses_the_same_history_anchor_and_weights(self):
        inputs = self.stable_inputs()
        inputs["forecast_bull_roe"] = [23.0, 24.0, 25.0]
        inputs["forecast_bull_roa"] = [11.5, 12.0, 12.5]
        output = calculate(**inputs)
        self.assertAlmostEqual(output["roe_percent"]["normalized_bull"],
                               0.5 * 19.142857142857142 + 0.2 * 23 + 0.2 * 24 + 0.1 * 25)
        self.assertAlmostEqual(output["roa_percent"]["normalized_bull"],
                               0.5 * output["roa_percent"]["historical_anchor_used_for_normalized_neutral"]
                               + 0.2 * 11.5 + 0.2 * 12.0 + 0.1 * 12.5)

    def test_medium_confidence_keeps_stable_fifty_fifty_weights(self):
        inputs = self.stable_inputs()
        inputs["forecast_confidence"] = "medium"
        output = calculate(**inputs)
        self.assertAlmostEqual(output["weights"]["history_share"], 0.50)
        self.assertAlmostEqual(output["weights"]["forecast_share"], 0.50)
        self.assertAlmostEqual(output["roe_percent"]["normalized_neutral"], 19.97142857142857)
        self.assertAlmostEqual(output["roe_percent"]["normalized_bear"], 18.47142857142857)

    def test_moutai_regression_matches_confirmed_rule(self):
        output = calculate(
            company_type="stable",
            historical_roe=[34.20, 36.03, 32.52],
            forecast_base_roe=[32.1408289776, 31.6949142028, 31.3925428791],
            forecast_bear_roe=[30.3921952791, 26.9858428756, 24.7978862043],
            current_weak_roe=32.52,
            stable_years_comparable="confirmed",
        )
        self.assertAlmostEqual(output["roe_percent"]["normalized_neutral"], 32.1664029240)
        self.assertAlmostEqual(output["roe_percent"]["normalized_bear"], 30.2153962514)
        self.assertEqual(
            output["weights"]["forecast_base_nearest_to_farthest"],
            [0.20, 0.20, 0.10],
        )

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
