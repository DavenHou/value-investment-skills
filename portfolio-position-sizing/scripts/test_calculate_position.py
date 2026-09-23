import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("calculate_position.py")


class TrancheStressTest(unittest.TestCase):
    def test_cash_weighted_ladder_and_path_loss_are_separate(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "100",
                "--stress-loss-low-percent", "42.3", "--stress-loss-high-percent", "61.5",
                "--tranche", "4@45.45", "--tranche", "6@42.57",
                "--stress-price-low", "17.48", "--stress-price-high", "26.22",
            ], check=True, text=True, capture_output=True
        )
        stress = json.loads(completed.stdout)["tranche_stress"]
        self.assertEqual(stress["total_planned_weight_percent"], 10)
        self.assertAlmostEqual(
            stress["lower_stress"]["completed_ladder_weighted_average_cost"], 43.68, places=2
        )
        self.assertAlmostEqual(
            stress["lower_stress"]["completed_ladder_loss_percent"], 59.979, places=3
        )
        self.assertAlmostEqual(
            stress["lower_stress"]["completed_ladder_loss_percent_of_portfolio"], 5.9979, places=4
        )
        self.assertAlmostEqual(
            stress["lower_stress"]["per_tranche"][0]["loss_percent_of_tranche"], 61.5402, places=3
        )

    def test_completed_ladder_drawdown_limit_does_not_turn_into_position_cap(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--stress-loss-low-percent", "42.3", "--stress-loss-high-percent", "61.5",
                "--valuation-suggested-cap-percent", "20",
                "--tranche", "4@45.45", "--tranche", "6@42.57",
                "--stress-price-low", "17.48", "--stress-price-high", "26.22",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["completed_ladder_drawdown_gate"]["passed"])
        self.assertAlmostEqual(
            result["completed_ladder_drawdown_gate"]["worst_drawdown_percent"], 59.979, places=3
        )
        self.assertEqual(result["effective_cap_percent"], 20)
        self.assertNotIn("completed_ladder_drawdown", result["binding_constraint"])

    def test_completed_ladder_drawdown_at_user_limit_passes(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "50",
                "--tranche", "20@100",
                "--stress-price-low", "50", "--stress-price-high", "50",
            ], check=True, text=True, capture_output=True
        )
        gate = json.loads(completed.stdout)["completed_ladder_drawdown_gate"]
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["limit_percent"], 50)
        self.assertEqual(gate["worst_drawdown_percent"], 50)


class UserPolicySemanticsTest(unittest.TestCase):
    def test_missing_portfolio_risk_budget_is_non_binding(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--stress-loss-low-percent", "40", "--stress-loss-high-percent", "60",
                "--valuation-suggested-cap-percent", "20",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertIsNone(result["conservative_formula_cap_percent"])
        self.assertEqual(result["portfolio_risk_budget_status"], "not_selected_sensitivity_only")
        self.assertEqual(result["effective_cap_percent"], 20)
        self.assertEqual(result["binding_constraint"], ["valuation_suggested_market_adjusted"])

    def test_user_can_assume_stock_count_is_within_policy_for_this_run(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--stress-loss-low-percent", "40", "--stress-loss-high-percent", "60",
                "--assume-stock-count-within-policy", "--new-position",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result["new_position_slot_available"])
        self.assertEqual(result["stock_count_assessment"], "assumed_within_policy_by_user")

    def test_fewer_than_five_positions_keeps_unallocated_capital_in_cash(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "40", "--stress-loss-high-percent", "60",
                "--current-stock-count", "3", "--new-position",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["stock_count_assessment"], "below_preferred_range_cash_allowed")
        self.assertEqual(result["unallocated_capital_policy"], "hold_cash_do_not_fill_to_minimum")

    def test_current_policy_defaults(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "100",
                "--stress-loss-low-percent", "40", "--stress-loss-high-percent", "60",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["inputs"]["preferred_stock_count_low"], 5)
        self.assertEqual(result["inputs"]["preferred_stock_count_target"], 6)
        self.assertEqual(result["inputs"]["preferred_stock_count_high"], 8)
        self.assertIn("single_name", result["binding_constraint"])

    def test_ninth_position_requires_explicit_exception_evidence(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "60",
                "--current-stock-count", "8", "--qualified-undervalued-count", "9",
                "--new-position",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["new_position_slot_available"])
        self.assertEqual(
            result["stock_count_assessment"],
            "nine_to_ten_replacement_or_risk_improvement_required",
        )

    def test_ninth_position_can_use_evidence_backed_exception(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "60",
                "--current-stock-count", "8", "--qualified-undervalued-count", "9",
                "--new-position", "--above-preferred-expansion-justified",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result["new_position_slot_available"])
        self.assertEqual(
            result["stock_count_assessment"], "nine_to_ten_exception_evidence_supported"
        )

    def test_eleventh_position_is_outside_exception_zone(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "60",
                "--current-stock-count", "10", "--qualified-undervalued-count", "11",
                "--new-position", "--above-preferred-expansion-justified",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["new_position_slot_available"])
        self.assertEqual(result["stock_count_assessment"], "above_policy_exception_zone")

    def test_legacy_comparison_exposes_ninth_position_policy_change(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "60",
                "--current-stock-count", "8", "--qualified-undervalued-count", "9",
                "--new-position", "--compare-legacy-rules",
            ], check=True, text=True, capture_output=True
        )
        comparison = json.loads(completed.stdout)["rule_comparison"]
        self.assertEqual(comparison["old_rules"]["preferred_stock_count_range"], [6, 10])
        self.assertEqual(comparison["new_rules"]["preferred_stock_count_range"], [5, 8])
        self.assertTrue(comparison["old_rules"]["new_position_slot_available"])
        self.assertFalse(comparison["new_rules"]["new_position_slot_available"])
        self.assertTrue(comparison["new_position_slot_changed"])
        self.assertIn("nine_to_ten_evidence_gate_changed_slot", comparison["change_reasons"])

    def test_legacy_comparison_does_not_extend_beyond_ten_positions(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "1",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "60",
                "--current-stock-count", "10", "--qualified-undervalued-count", "11",
                "--new-position", "--compare-legacy-rules",
            ], check=True, text=True, capture_output=True
        )
        comparison = json.loads(completed.stdout)["rule_comparison"]
        self.assertFalse(comparison["old_rules"]["new_position_slot_available"])


class KellyReferenceTest(unittest.TestCase):
    def run_calculator(self, *extra_args, check=True):
        return subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "100",
                "--stress-loss-low-percent", "50", "--stress-loss-high-percent", "100",
                *extra_args,
            ], check=check, text=True, capture_output=True
        )

    def usable_audit_args(self):
        return [
            "--kelly-status", "usable",
            "--kelly-input-basis", "conservative",
            "--kelly-strategy-scope", "us_large_cap_value",
            "--kelly-sample-cutoff-date", "2026-09-01",
            "--kelly-probability-source", "same_strategy_ledger",
            "--kelly-probability-confidence-method", "lower_95_bound",
            "--kelly-payoff-conservative-method", "win_low_loss_high",
            "--kelly-horizon", "three_years",
            "--kelly-exit-rule", "predefined_thesis_exit",
            "--kelly-raw-sample-size", "120",
            "--kelly-effective-sample-size", "80",
        ]

    def test_binary_source_example_full_kelly_is_25_percent(self):
        completed = self.run_calculator(
            *self.usable_audit_args(),
            "--kelly-win-probability-percent", "50",
            "--kelly-win-return-multiple", "2",
            "--kelly-loss-return-multiple", "1",
            "--kelly-adopted-fraction", "1",
        )
        result = json.loads(completed.stdout)
        kelly = result["kelly_reference"]
        self.assertEqual(kelly["unconstrained_full_kelly_percent"], 25)
        self.assertEqual(kelly["full_kelly_long_only_percent"], 25)
        self.assertEqual(kelly["half_kelly_percent"], 12.5)
        self.assertEqual(kelly["quarter_kelly_percent"], 6.25)
        self.assertTrue(kelly["cap_active"])
        self.assertEqual(result["effective_cap_percent"], 25)
        self.assertIn("kelly_reference", result["binding_constraint"])

    def test_negative_conservative_edge_binds_at_zero_when_adopted(self):
        completed = self.run_calculator(
            *self.usable_audit_args(),
            "--kelly-win-probability-percent", "30",
            "--kelly-win-return-multiple", "1",
            "--kelly-loss-return-multiple", "1",
            "--kelly-adopted-fraction", "0.5",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["kelly_reference"]["full_kelly_long_only_percent"], 0)
        self.assertEqual(result["effective_cap_percent"], 0)

    def test_usable_kelly_without_selected_fraction_stays_inactive(self):
        completed = self.run_calculator(
            *self.usable_audit_args(),
            "--kelly-win-probability-percent", "50",
            "--kelly-win-return-multiple", "2",
            "--kelly-loss-return-multiple", "1",
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["kelly_reference"]["cap_active"])
        self.assertIsNone(result["kelly_reference"]["adopted_cap_percent"])
        self.assertEqual(result["effective_cap_percent"], 35)

    def test_legacy_comparison_shows_when_kelly_reduces_the_cap(self):
        completed = self.run_calculator(
            *self.usable_audit_args(),
            "--kelly-win-probability-percent", "50",
            "--kelly-win-return-multiple", "2",
            "--kelly-loss-return-multiple", "1",
            "--kelly-adopted-fraction", "0.5",
            "--compare-legacy-rules",
        )
        comparison = json.loads(completed.stdout)["rule_comparison"]
        self.assertEqual(comparison["old_rules"]["effective_cap_percent"], 35)
        self.assertEqual(comparison["new_rules"]["effective_cap_percent"], 12.5)
        self.assertEqual(comparison["effective_cap_delta_percent"], -22.5)
        self.assertEqual(comparison["kelly_decision_role"], "binding_reduced_cap")
        self.assertTrue(comparison["kelly_participated_in_final_decision"])

    def test_illustrative_kelly_never_becomes_a_cap(self):
        completed = self.run_calculator(
            "--kelly-status", "illustrative",
            "--kelly-input-basis", "subjective_scenario",
            "--kelly-win-probability-percent", "50",
            "--kelly-win-return-multiple", "2",
            "--kelly-loss-return-multiple", "1",
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["kelly_reference"]["cap_active"])
        self.assertEqual(result["effective_cap_percent"], 35)
        self.assertNotIn("kelly_reference", result["binding_constraint"])

    def test_multi_scenario_log_optimum_matches_binary_example(self):
        completed = self.run_calculator(
            *self.usable_audit_args(),
            "--kelly-scenario", "50@2",
            "--kelly-scenario", "50@-1",
            "--kelly-adopted-fraction", "1",
        )
        result = json.loads(completed.stdout)
        self.assertAlmostEqual(
            result["kelly_reference"]["full_kelly_long_only_percent"], 25, places=4
        )
        self.assertEqual(result["kelly_reference"]["outcome_model"], "multi_scenario")

    def test_usable_kelly_rejects_missing_audit_fields(self):
        completed = self.run_calculator(
            "--kelly-status", "usable",
            "--kelly-input-basis", "conservative",
            "--kelly-win-probability-percent", "50",
            "--kelly-win-return-multiple", "2",
            "--kelly-loss-return-multiple", "1",
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("complete sample", completed.stderr)

    def test_multi_scenario_probabilities_must_sum_to_100(self):
        completed = self.run_calculator(
            "--kelly-status", "illustrative",
            "--kelly-input-basis", "subjective_scenario",
            "--kelly-scenario", "40@2",
            "--kelly-scenario", "40@-1",
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sum to 100", completed.stderr)



class QualityCapTests(unittest.TestCase):
    def test_ladder_bands(self):
        from calculate_position import quality_cap
        self.assertEqual(quality_cap(54)["cap_percent"], 0.0)   # 第27条 底线 55
        self.assertEqual(quality_cap(59)["cap_percent"], 5.0)   # 55–59 降级候选
        self.assertEqual(quality_cap(60)["cap_percent"], 10.0)
        self.assertEqual(quality_cap(70)["cap_percent"], 20.0)
        self.assertEqual(quality_cap(78)["cap_percent"], 28.0)
        self.assertEqual(quality_cap(85)["cap_percent"], 35.0)
        self.assertEqual(quality_cap(100)["cap_percent"], 35.0)

    def test_missing_score_blocks_new_position(self):
        from calculate_position import quality_cap
        self.assertEqual(quality_cap(None)["cap_percent"], 0.0)
        self.assertEqual(quality_cap(None)["band"], "insufficient")

    def test_worst_case_reports_both_legs(self):
        from calculate_position import worst_case_preview
        w = worst_case_preview(position_percent=20.0, entry_price=100.0,
                               deep_value_price=70.0, bear_price=50.0)
        self.assertAlmostEqual(w["to_deep_value"]["stock_drawdown_percent"], 30.0)
        self.assertAlmostEqual(w["to_deep_value"]["portfolio_drag_percent"], 6.0)
        self.assertAlmostEqual(w["to_bear_case"]["portfolio_drag_percent"], 10.0)


class ScaledLadderTests(unittest.TestCase):
    def test_35_percent_cap_reproduces_the_original_ladder(self):
        from calculate_position import scaled_ladder
        L = {t["tier"]: t["cumulative_percent"] for t in scaled_ladder(35.0)}
        self.assertAlmostEqual(L["首仓"][0], 4.2, places=1)
        self.assertAlmostEqual(L["首仓"][1], 5.95, places=2)
        self.assertAlmostEqual(L["主要加仓"][1], 15.05, places=2)
        self.assertAlmostEqual(L["深度价值"][1], 35.0, places=1)

    def test_lower_cap_scales_every_tier_not_just_the_deep_ones(self):
        """截断会让首仓在上限 10% 时仍是 4%-6%；缩放必须把它压到 1.2%-1.7%。"""
        from calculate_position import scaled_ladder
        L = {t["tier"]: t["cumulative_percent"] for t in scaled_ladder(10.0)}
        self.assertAlmostEqual(L["首仓"][0], 1.2, places=1)
        self.assertAlmostEqual(L["首仓"][1], 1.7, places=1)
        self.assertAlmostEqual(L["深度价值"][1], 10.0, places=1)
        self.assertLess(L["首仓"][1], 4.0)

    def test_zero_cap_blocks_every_tier(self):
        from calculate_position import scaled_ladder
        for t in scaled_ladder(0.0):
            self.assertEqual(t["status"], "blocked_by_quality_gate")


class ChecklistTests(unittest.TestCase):
    # --- 第26条 前置快筛（2026-09-18）---------------------------------------

    def test_prescreen_0a_stops_on_pb_above_eight(self):
        from calculate_position import prescreen
        r = prescreen(pb=13.01, pe_ttm=23.33, roe_ttm_percent=62.17, company_type="stable")
        self.assertTrue(r["stop"]); self.assertEqual(r["reason"], "pb_ceiling_breach")

    def test_prescreen_0b_stops_on_verification_pr_above_half(self):
        """特步：PB 0.75 过 0a，核验PR 0.5235 > 0.50 → 停在 0b。"""
        from calculate_position import prescreen
        r = prescreen(pb=0.7522, pe_ttm=6.442, roe_ttm_percent=12.306, company_type="stable")
        self.assertTrue(r["stop"])
        self.assertEqual(r["reason"], "verification_pr_above_entry")
        self.assertAlmostEqual(r["verification_pr"], 0.5235, places=3)

    def test_prescreen_passes_deck(self):
        """DECK 2026-09-18 截止日锁定快照：两道都过，进入完整估值。"""
        from calculate_position import prescreen
        r = prescreen(pb=4.6143, pe_ttm=78.43 / 7.03,
                      roe_ttm_percent=40.554, company_type="stable")
        self.assertFalse(r["stop"]); self.assertEqual(r["reason"], "prescreen_pass")

    def test_prescreen_0b_disabled_for_cyclicals(self):
        """周期股低谷 PE_TTM 虚高，0b 会在最便宜时误杀，必须禁用。"""
        from calculate_position import prescreen
        r = prescreen(pb=0.8, pe_ttm=40.0, roe_ttm_percent=2.0, company_type="cyclical")
        self.assertFalse(r["stop"]); self.assertEqual(r["reason"], "cyclical_0b_excluded")

    def test_prescreen_skipped_for_existing_holdings(self):
        """已有持仓：8PB 是买入端禁令，跳过会让持仓失去退出监控。"""
        from calculate_position import prescreen
        r = prescreen(pb=23.13, pe_ttm=27.46, roe_ttm_percent=99.86,
                      company_type="technology", is_existing_holding=True)
        self.assertFalse(r["stop"])
        self.assertEqual(r["reason"], "existing_holding_full_pipeline")

    def test_prescreen_not_applicable_when_roe_non_positive(self):
        from calculate_position import prescreen
        r = prescreen(pb=2.0, pe_ttm=30.0, roe_ttm_percent=-5.0, company_type="hybrid_platform")
        self.assertFalse(r["stop"])
        self.assertEqual(r["reason"], "verification_pr_not_applicable")

    def test_verification_pr_is_lower_bound_of_decision_pr(self):
        """数值守卫：执行ROE = min(…, ROE_TTM) ≤ ROE_TTM ⟹ 决策PR ≥ 核验PR。

        文本测试挡不住"公式写对了但没执行"——PB形误用那次
        test_rule_consistency 一直是绿的。这条必须是数值的。
        """
        pe = 12.5
        for roe_ttm, others in ((40.0, [35.0, 38.0]), (12.3, [13.55, 11.389]),
                                (99.86, [89.279, 67.955]), (62.17, [30.13])):
            decision_roe = min([roe_ttm] + others)
            self.assertLessEqual(decision_roe, roe_ttm)
            self.assertGreaterEqual(pe / decision_roe, pe / roe_ttm)

    # --- 第20条修订 质量门槛 55 ---------------------------------------------

    def test_quality_floor_is_fifty_five(self):
        from calculate_position import quality_cap
        self.assertEqual(quality_cap(54.0)["cap_percent"], 0.0)
        self.assertEqual(quality_cap(54.0)["band"], "fail")
        self.assertEqual(quality_cap(55.0)["cap_percent"], 5.0)
        self.assertEqual(quality_cap(56.1)["band"], "pass_downgraded")
        self.assertEqual(quality_cap(59.9)["cap_percent"], 5.0)

    def test_quality_bands_above_sixty_unchanged(self):
        from calculate_position import quality_cap
        for score, cap in ((60.0, 10.0), (69.9, 10.0), (73.9, 20.0),
                           (79.6, 28.0), (80.2, 28.0), (85.0, 35.0)):
            self.assertEqual(quality_cap(score)["cap_percent"], cap, msg=str(score))

    def test_untriggered_items_still_print(self):
        from calculate_position import calibration_checklist
        items = calibration_checklist(market_coefficient_c=1.0, company_type="growth",
                                      payout_percent=51.4)
        names = [i["item"] for i in items]
        self.assertIn("市场系数 c（第23条：买卖两端同乘）", names)
        self.assertIn("股息支付率修正 N", names)
        self.assertIn("市场系数 c（第23条：买卖两端同乘）", names)
        n = next(i for i in items if i["item"] == "股息支付率修正 N")
        self.assertFalse(n["applies"])
        self.assertIn("成长", n["note"])

    def test_payout_over_fifty_gives_n_equal_one(self):
        from calculate_position import calibration_checklist
        items = calibration_checklist(market_coefficient_c=1.0, company_type="stable",
                                      payout_percent=51.4)
        n = next(i for i in items if i["item"] == "股息支付率修正 N")
        self.assertTrue(n["applies"])
        self.assertEqual(n["value"], 1.0)

    def test_market_coefficient_is_consumed_from_valuation_handoff(self):
        from calculate_position import calibration_checklist
        for expected in (1.0, 0.8314):
            items = calibration_checklist(market_coefficient_c=expected,
                                          company_type="stable", payout_percent=40.0)
            c = next(i for i in items if i["item"].startswith("市场系数 c"))
            self.assertEqual(c["value"], expected)
            self.assertIn("消费估值交接", c["note"])


# 2026-09-18：这一行原本卡在文件中间，直接执行只收集到它之前定义的类，
# 后半段用例被静默跳过。交接文档里的回归命令用的正是直接执行。
if __name__ == "__main__":
    unittest.main()
