#!/usr/bin/env python3

import unittest

from calculate_valuation import (
    calculate,
    major_earnings_decline_protection,
    market_coefficient,
    pb_gate,
    recomputed_roe,
    trailing_twelve_month_eps,
)


class CalculateValuationTests(unittest.TestCase):
    def test_dividend_yield_selects_bear_neutral_bull_at_strict_boundaries(self):
        inputs = dict(company_type="stable", pe_ttm=18.0, roe_ttm_percent=20.0,
                      normalized_roe_percent=14.0, pessimistic_anchor_roe_percent=10.0,
                      optimistic_normalized_roe_percent=16.0, current_price=60.0)
        for dividend_yield, tier, roe in ((5.0, "bear", 10.0), (5.01, "neutral", 14.0),
                                          (6.0, "neutral", 14.0), (6.01, "bull", 16.0)):
            with self.subTest(dividend_yield=dividend_yield):
                result = calculate(**inputs, dividend_yield_percent=dividend_yield)
                self.assertEqual(result["forecast_tier_selection"]["tier"], tier)
                self.assertEqual(result["decision"]["decision_roe_percent"], roe)
                self.assertAlmostEqual(result["decision"]["decision_pr"], 18.0 / roe)
                self.assertAlmostEqual(result["decision"]["target_price"]["buy"]["0.5"],
                                       60.0 * 0.5 * roe / 18.0)

    def test_historical_roe_remains_a_cap_after_dividend_selection(self):
        result = calculate(company_type="stable", pe_ttm=18.0, roe_ttm_percent=20.0,
                           historical_roe_percent=12.0, normalized_roe_percent=14.0,
                           pessimistic_anchor_roe_percent=10.0,
                           optimistic_normalized_roe_percent=16.0,
                           dividend_yield_percent=6.1)
        self.assertEqual(result["forecast_tier_selection"]["tier"], "bull")
        self.assertEqual(result["decision"]["decision_roe_percent"], 12.0)
        self.assertEqual(result["decision"]["conservative_anchor_used"], "historical")

    def test_missing_required_bull_roe_does_not_invent_a_value(self):
        result = calculate(company_type="stable", pe_ttm=18.0, roe_ttm_percent=20.0,
                           normalized_roe_percent=14.0, pessimistic_anchor_roe_percent=10.0,
                           dividend_yield_percent=6.1)
        self.assertEqual(result["forecast_tier_selection"]["tier"], "bull")
        self.assertIsNone(result["decision"])

    def test_missing_dividend_and_bear_handoff_is_unselected(self):
        result = calculate(company_type="stable", pe_ttm=18.0, roe_ttm_percent=20.0,
                           normalized_roe_percent=14.0)
        self.assertEqual(result["forecast_tier_selection"]["status"], "unselected")

    def test_cyclical_high_dividend_uses_bull_forecast_in_pb_path(self):
        result = calculate(company_type="cyclical", pb=1.5, roe_percent=20.0,
                           normalized_roe_percent=14.0, pessimistic_anchor_roe_percent=10.0,
                           optimistic_normalized_roe_percent=16.0,
                           dividend_yield_percent=6.1)
        self.assertEqual(result["decision"]["forecast_tier"], "bull")
        self.assertEqual(result["decision"]["decision_roe_percent"], 16.0)
        self.assertAlmostEqual(result["decision"]["decision_pr"], 100 * 1.5 / 16**2)

    def test_major_earnings_decline_threshold_and_roe_override(self):
        inputs = dict(company_type="stable", pe_ttm=12.0, roe_ttm_percent=12.0,
                      normalized_roe_percent=14.0, pessimistic_anchor_roe_percent=10.0,
                      optimistic_normalized_roe_percent=16.0,
                      dividend_yield_percent=6.1,
                      prior_quarter_core_profits=[25.0] * 4)
        for current, triggered in ((90.0, False), (80.1, False),
                                   (80.0, True), (70.0, True)):
            with self.subTest(current=current):
                result = calculate(**inputs, current_quarter_core_profits=[current / 4] * 4)
                guard = result["major_earnings_decline_protection"]
                self.assertEqual(guard["triggered"], triggered)
                self.assertAlmostEqual(guard["yoy_percent"], current - 100.0)
                if triggered:
                    self.assertEqual(result["decision"]["decision_roe_percent"], 10.0)
                    self.assertEqual(result["decision"]["normalized_roe_percent"], 10.0)
                    self.assertEqual(guard["note"],
                                     "TTM扣非净利润同比下降≥20%，估值切换至悲观预测。")
                else:
                    self.assertEqual(result["forecast_tier_selection"]["tier"], "bull")
                    self.assertEqual(result["decision"]["normalized_roe_percent"], 16.0)
                    self.assertEqual(result["decision"]["decision_roe_percent"], 12.0)

        missing = calculate(**inputs, current_quarter_core_profits=None)
        self.assertEqual(missing["major_earnings_decline_protection"]["status"],
                         "数据不足，无法判断")
        self.assertFalse(missing["major_earnings_decline_protection"]["triggered"])
        abnormal = major_earnings_decline_protection([20.0] * 4, [0.0] * 4)
        self.assertEqual(abnormal["status"], "基期异常，无法使用正常同比判断")
        self.assertEqual(major_earnings_decline_protection([20.0] * 3, [25.0] * 4)["status"],
                         "数据不足，无法判断")
        self.assertEqual(major_earnings_decline_protection([20.0, None, 20.0, 20.0],
                                                            [25.0] * 4)["status"],
                         "数据不足，无法判断")

    def test_major_decline_requires_bearish_handoff(self):
        result = calculate(company_type="stable", pe_ttm=12.0,
                           roe_ttm_percent=12.0, normalized_roe_percent=14.0,
                           current_quarter_core_profits=[20.0] * 4,
                           prior_quarter_core_profits=[25.0] * 4)
        self.assertTrue(result["major_earnings_decline_protection"]["triggered"])
        self.assertIsNone(result["decision"])

    def test_payout_adjustment_requires_current_dividend_yield_gate(self):
        inputs = dict(company_type="stable", pe_ttm=12.0, roe_ttm_percent=12.0,
                      normalized_roe_percent=12.0, payout_percent=30.0)
        low_yield = calculate(**inputs, dividend_yield_percent=3.08)
        high_yield = calculate(**inputs, dividend_yield_percent=5.10)
        self.assertEqual(low_yield["payout_adjustment_n"], 1.0)
        self.assertAlmostEqual(high_yield["payout_adjustment_n"], 50.0 / 30.0)

    def test_deck_cutoff_locked_noncyclical_calculation(self):
        ttm_eps = trailing_twelve_month_eps(
            latest_full_year_diluted_eps=7.02,
            prior_comparable_ytd_diluted_eps=0.93,
            current_ytd_diluted_eps=0.94,
        )
        normal = recomputed_roe(
            ttm_net_income=1014.840,
            ending_equity=2301.682,
            cumulative_buyback=2369.750,
            company_type="stable",
            financial_cutoff_date="2026-06-30",
            buyback_window_start_date="2023-07-01",
            buyback_window_end_date="2026-06-30",
        )
        result = calculate(
            company_type="stable",
            current_price=78.43,
            pe_ttm=78.43 / ttm_eps,
            roe_ttm_percent=40.554,
            normalized_roe_percent=30.0,
            normal_capital_roe_percent=normal["recomputed_roe_percent"],
        )
        decision = result["decision"]
        self.assertAlmostEqual(ttm_eps, 7.03)
        self.assertAlmostEqual(normal["recomputed_roe_percent"], 21.7243877252)
        self.assertEqual(decision["conservative_anchor_used"], "normal_capital")
        self.assertAlmostEqual(decision["decision_pr"], 0.5135459928)
        self.assertAlmostEqual(decision["target_price"]["buy"]["0.5"], 76.3612, places=4)

    def test_normal_capital_roe_rejects_cross_cutoff_inputs(self):
        with self.assertRaisesRegex(ValueError, "window end must equal"):
            recomputed_roe(
                ttm_net_income=1014.840,
                ending_equity=2301.682,
                cumulative_buyback=2369.750,
                company_type="stable",
                financial_cutoff_date="2026-06-30",
                buyback_window_start_date="2023-04-01",
                buyback_window_end_date="2026-03-31",
            )
        with self.assertRaisesRegex(ValueError, "exact rolling 3-year"):
            recomputed_roe(
                ttm_net_income=1014.840,
                ending_equity=2301.682,
                cumulative_buyback=2369.750,
                company_type="stable",
                financial_cutoff_date="2026-06-30",
                buyback_window_start_date="2023-04-01",
                buyback_window_end_date="2026-06-30",
            )

    def test_china_want_want_hk_noncyclical_smoke(self):
        """2026-09-12 本地快照：只验证新口径，不作当前投资结论。"""
        result = calculate(
            company_type="stable",
            listing_market="hk",
            current_price=2.835,
            pe_ttm=7.925636007827788,
            roe_ttm_percent=20.2897950586787,
            pb=1.4817408756644315,
            normalized_roe_percent=18.695545369494432,
            pessimistic_anchor_roe_percent=13.6967055420816,
            dividend_yield_percent=3.81305114638448,
            tax_percent=20.0,
        )
        decision = result["decision"]
        expected_c = 0.90 * (1 - 3.81305114638448 * 0.20 / 10)
        self.assertAlmostEqual(result["high_pr_line"]["e_market"], expected_c, places=4)
        self.assertAlmostEqual(decision["decision_roe_percent"], 13.6967055420816)
        self.assertAlmostEqual(
            decision["decision_pr"], 7.925636007827788 / 13.6967055420816
        )
        self.assertEqual(decision["decision_pr_basis"], "non_cyclical_pe_form")
        self.assertEqual(decision["buy_tier"]["status"], "above_all_tiers")

    def test_aligned_ttm_snapshot(self):
        result = calculate(pe_ttm=14.7, roe_ttm_percent=31, current_price=100)
        self.assertEqual(result["calculation_basis"], "aligned_ttm")
        self.assertAlmostEqual(result["base_pr"]["from_pe_ttm"], 14.7 / 31)
        self.assertIn("0.5", result["target_map"])

    def test_rejects_half_ttm_pair(self):
        with self.assertRaisesRegex(ValueError, "must be provided together"):
            calculate(pe_ttm=14.7, roe_percent=31)

    def test_normalized_pb_path_remains_available(self):
        result = calculate(pb=0.96, roe_percent=15.88, listing_market="hk",
                           dividend_yield_percent=0.0)
        self.assertEqual(result["calculation_basis"], "normalized_or_unspecified_period")
        self.assertAlmostEqual(result["base_pr"]["from_pb"], 100 * 0.96 / 15.88**2)
        # 买卖两端同乘 c：无股息时 c=0.90。
        self.assertIn("0.45", result["target_map"])
        self.assertIn("0.9", result["target_map"])

    def test_rejects_non_positive_market_coefficient(self):
        with self.assertRaisesRegex(ValueError, "market coefficient"):
            market_coefficient(
                listing_market="hk", dividend_yield_percent=100.0, tax_percent=99.0
            )

    def test_cycle_case_flags_material_gap_without_fixed_half_sale(self):
        result = calculate(
            pb=1.14,
            roe_percent=14.59,
            listing_market="a",
            cycle_current_run_rate_roe_percent=10.80,
            normalized_roe_percent=14.59,
            cycle_bear_roe_percent=10.80,
        )
        conflict = result["cycle_anchor_conflict"]
        self.assertEqual(conflict["status"], "material_gap")
        self.assertAlmostEqual(conflict["pr_by_anchor"]["current_run_rate"], 0.9773662551)
        self.assertAlmostEqual(conflict["pr_by_anchor"]["normalized"], 100 * 1.14 / 14.59**2)
        self.assertFalse(conflict["fixed_half_sale_rule"])

    def test_hk_regime_split_pauses_new_positions(self):
        result = calculate(
            pb=0.95,
            roe_percent=16.0,
            listing_market="hk",
            dividend_yield_percent=8.40,
            cycle_current_run_rate_roe_percent=10.80,
            normalized_roe_percent=16.0,
            cycle_bear_roe_percent=10.80,
        )
        conflict = result["cycle_anchor_conflict"]
        self.assertEqual(conflict["status"], "regime_split")
        self.assertAlmostEqual(conflict["first_entry_pr"], 0.50 * 0.7488)
        self.assertEqual(conflict["first_entry_normalized"], 0.50)
        self.assertEqual(conflict["realize_line_normalized"], 0.80)
        self.assertTrue(conflict["default_half_sale_on_regime_split"])
        self.assertIn("pause_new_positions", conflict["action_effect"])

    def test_partial_cycle_inputs_are_insufficient(self):
        result = calculate(
            pb=1.0,
            roe_percent=12.0,
            cycle_current_run_rate_roe_percent=10.0,
        )
        self.assertEqual(result["cycle_anchor_conflict"]["status"], "insufficient")
        self.assertEqual(
            result["cycle_anchor_conflict"]["missing_inputs"], ["normalized", "bear"]
        )

    def test_cyclical_decision_uses_five_year_low_plus_forecast_handoff(self):
        result = calculate(
            pb=1.14,
            roe_percent=14.59,
            listing_market="a",
            current_price=40.0,
            cycle_current_run_rate_roe_percent=10.80,
            normalized_roe_percent=14.59,
            cycle_bear_roe_percent=10.80,
            pessimistic_anchor_roe_percent=9.5,
        )
        decision = result["decision"]
        self.assertEqual(decision["policy_version"], "single-decision-pr-v2")
        self.assertAlmostEqual(decision["decision_pr"], 100 * 1.14 / 9.5**2)
        self.assertEqual(decision["conservative_anchor_used"], "five_year_low_plus_bear_forecast")
        self.assertTrue(decision["forecast_in_action_line"])
        self.assertFalse(decision["second_action_pr_present"])
        self.assertFalse(decision["recomputable_at_historical_peaks"])
        self.assertAlmostEqual(decision["target_pb"]["0.5"], 0.5 * 9.5**2 / 100)
        self.assertAlmostEqual(
            decision["target_price"]["buy"]["0.5"], 40.0 * 0.5 / decision["decision_pr"]
        )

    def test_same_formula_reproduces_a_historical_peak(self):
        """S/H/M and the current PR must land on one number line."""
        current = calculate(pb=1.14, roe_percent=14.59, normalized_roe_percent=14.59,
                            pessimistic_anchor_roe_percent=9.5)
        peak = calculate(pb=2.30, roe_percent=13.10, normalized_roe_percent=13.10,
                         pessimistic_anchor_roe_percent=8.0)
        self.assertEqual(
            current["decision"]["decision_pr_basis"],
            peak["decision"]["decision_pr_basis"],
        )
        self.assertAlmostEqual(peak["decision"]["decision_pr"], 100 * 2.30 / 8.0**2)
        self.assertLess(current["decision"]["decision_pr"], peak["decision"]["decision_pr"])

    def test_cyclical_peak_needs_asof_forecast_provenance(self):
        inputs = dict(pb=1.14, roe_percent=14.59, normalized_roe_percent=14.59,
                      pessimistic_anchor_roe_percent=9.5, historical_peak_pr=0.4)
        unverified = calculate(**inputs)
        verified = calculate(**inputs, historical_peak_asof_forecast_verified=True)
        self.assertEqual(unverified["high_pr_line"]["effective_high_pr"], 1.0)
        self.assertEqual(verified["high_pr_line"]["effective_high_pr"], 0.4)
        self.assertFalse(unverified["decision"]["recomputable_at_historical_peaks"])

    def test_cyclical_requires_formal_bear_roe_handoff(self):
        result = calculate(pb=1.0, roe_percent=10.0, normalized_roe_percent=10.0)
        self.assertEqual(result["decision"]["decision_pr_status"], "insufficient")
        self.assertIn("formal_bear_roe_handoff", result["decision"]["missing_inputs"])

    def test_missing_pb_marks_decision_pr_insufficient(self):
        result = calculate(pe=10.0, roe_percent=12.0, normalized_roe_percent=12.0)
        self.assertEqual(result["decision"]["decision_pr_status"], "insufficient")
        self.assertIsNone(result["decision"]["decision_pr"])

    def test_guard_binds_when_current_roe_fell_below_the_anchor(self):
        """Gree case: 3y anchor 24.08%, TTM 19.08% -> no reversion discount."""
        result = calculate(
            company_type="stable",
            pe_ttm=7.7866,
            roe_ttm_percent=19.077,
            pb=1.4612,
            normalized_roe_percent=24.0833,
            current_price=38.74,
        )
        d = result["decision"]
        self.assertTrue(d["no_mean_reversion_guard"])
        self.assertAlmostEqual(d["gap_percent"], 20.787433615825073)
        self.assertAlmostEqual(d["decision_roe_percent"], 19.077)
        # 非周期股用 PE 形，分母取 min(执行ROE, ROE_TTM)
        self.assertEqual(d["decision_pr_basis"], "non_cyclical_pe_form")
        self.assertAlmostEqual(d["decision_pr"], 7.7866 / 19.077)
        # 保守优先把 PR 推向更贵的一侧
        self.assertGreater(d["decision_pr"], 7.7866 / 24.0833)

    def test_conservative_first_binds_even_inside_the_old_tolerance(self):
        """20% gap 门槛已被保守优先吸收：低一点也不白拿回归折扣。"""
        result = calculate(
            company_type="stable",
            pe_ttm=10.0,
            roe_ttm_percent=22.0,
            pb=2.2,
            normalized_roe_percent=24.0,
        )
        d = result["decision"]
        self.assertAlmostEqual(d["decision_roe_percent"], 22.0)
        self.assertFalse(d["material_gap_review_required"])  # gap 8.3% < 20%
        self.assertTrue(d["no_mean_reversion_guard"])

    def test_cyclical_takes_the_lowest_anchor(self):
        """周期股保守优先：跨周期锚与当前TTM 取低，不是守住跨周期锚。"""
        result = calculate(
            company_type="cyclical",
            pe_ttm=20.0,
            roe_ttm_percent=5.0,
            pb=1.0,
            normalized_roe_percent=15.0,
            pessimistic_anchor_roe_percent=9.0,
        )
        d = result["decision"]
        self.assertFalse(d["guard_applicable"])
        self.assertAlmostEqual(d["decision_roe_percent"], 5.0)
        self.assertEqual(d["conservative_anchor_used"], "ttm")
        self.assertEqual(d["cycle_anchor_candidates"], {"five_year_low_plus_bear_forecast": 9.0, "ttm": 5.0})

    def test_forecast_enters_only_through_the_pessimistic_anchor(self):
        """预测只有一个入口：混合悲观锚，且只能把PR 推贵。"""
        base = dict(company_type="stable", pe_ttm=8.0, roe_ttm_percent=19.0,
                    pb=1.5, normalized_roe_percent=24.0)
        plain = calculate(**base)
        tighter = calculate(**base, pessimistic_anchor_roe_percent=15.0)
        looser = calculate(**base, pessimistic_anchor_roe_percent=30.0)
        # 悲观锚更低 → PR 更贵
        self.assertGreater(tighter["decision"]["decision_pr"], plain["decision"]["decision_pr"])
        # 悲观锚更高 → 取低规则让它无效，PR 不变
        self.assertEqual(looser["decision"]["decision_pr"], plain["decision"]["decision_pr"])

    def test_pb_form_is_cyclical_only(self):
        """PB 形第二公式收归周期股；非周期用 PE 形。"""
        cyc = calculate(company_type="cyclical", pb=1.2, roe_percent=15.0,
                        normalized_roe_percent=15.0,
                        pessimistic_anchor_roe_percent=15.0)["decision"]
        self.assertEqual(cyc["decision_pr_basis"], "cyclical_pb_form")
        self.assertAlmostEqual(cyc["decision_pr"], 100 * 1.2 / 15.0**2)
        self.assertIsNotNone(cyc["target_pb"])
        for ct in ("stable", "technology", "financial"):
            d = calculate(company_type=ct, pb=1.2, pe_ttm=8.0, roe_ttm_percent=15.0,
                          normalized_roe_percent=15.0)["decision"]
            self.assertEqual(d["decision_pr_basis"], "non_cyclical_pe_form")
            self.assertAlmostEqual(d["decision_pr"], 8.0 / 15.0)
            self.assertIsNone(d["target_pb"])

    def test_non_cyclical_without_pe_is_insufficient(self):
        d = calculate(company_type="stable", pb=1.2, roe_percent=15.0,
                      normalized_roe_percent=15.0)["decision"]
        self.assertEqual(d["decision_pr_status"], "insufficient")
        self.assertIn("pe_ttm", d["missing_inputs"])



class NormalizedScaleTests(unittest.TestCase):
    def test_buy_and_sell_lines_share_market_coefficient(self):
        a = calculate(pb=1.14, roe_percent=14.59, company_type="cyclical",
                      normalized_roe_percent=14.59, listing_market="a",
                      pessimistic_anchor_roe_percent=14.59)
        hk = calculate(pb=1.14, roe_percent=14.59, company_type="cyclical",
                       normalized_roe_percent=14.59, listing_market="hk",
                       pessimistic_anchor_roe_percent=14.59,
                       optimistic_normalized_roe_percent=14.59,
                       dividend_yield_percent=8.40)
        self.assertEqual(a["inputs"]["buy_targets_normalized_to_raw"]["0.5"], 0.5)
        self.assertEqual(hk["inputs"]["market_pr_factor"], 0.7488)
        self.assertAlmostEqual(
            hk["inputs"]["buy_targets_normalized_to_raw"]["0.5"], 0.5 * 0.7488
        )
        self.assertAlmostEqual(
            hk["inputs"]["sell_targets_normalized_to_raw"]["norm_1.0"], 0.7488
        )

    def test_normalized_position_puts_the_sell_line_at_one(self):
        hk = calculate(pb=1.14, roe_percent=14.59, company_type="cyclical",
                       normalized_roe_percent=14.59, listing_market="hk",
                       pessimistic_anchor_roe_percent=14.59,
                       optimistic_normalized_roe_percent=14.59,
                       dividend_yield_percent=8.40)
        d = hk["decision"]
        self.assertAlmostEqual(d["normalized_position"],
                               d["decision_pr"] / d["high_pr_line"]["effective_high_pr"])
        self.assertEqual(d["high_pr_line"]["effective_high_pr"], 0.7488)

    def test_dynamic_coefficient_is_numeric_and_shared(self):
        self.assertEqual(
            market_coefficient(listing_market="hk", dividend_yield_percent=8.40),
            0.7488,
        )
        r = calculate(
            pb=1.0,
            roe_percent=20.0,
            normalized_roe_percent=20.0,
            pessimistic_anchor_roe_percent=20.0,
            optimistic_normalized_roe_percent=20.0,
            listing_market="hk",
            dividend_yield_percent=8.40,
            current_price=100.0,
        )
        prices = r["decision"]["target_price"]
        self.assertAlmostEqual(prices["sell"]["norm_1.0"] / prices["buy"]["0.5"], 2.0)
        self.assertEqual(r["decision"]["high_pr_line"]["effective_high_pr"], 0.7488)

    def test_pb_over_eight_blocks_new_positions(self):
        """8PB 现在是一行禁令，实现在 pb_gate()（第 16 条把 domain_gate 换掉之后）。"""
        self.assertEqual(pb_gate(9.0)["action"], "no_new_position")
        self.assertEqual(pb_gate(9.0)["status"], "blocked")
        self.assertEqual(pb_gate(8.0)["action"], "proceed")
        self.assertEqual(pb_gate(None)["action"], "no_new_position")


class TargetNamespaceTests(unittest.TestCase):
    def test_buy_and_sell_prices_never_collide(self):
        """E=0.59 时 卖出 0.8×E=0.472 会与买入档撞键，必须分开记名。"""
        r = calculate(company_type="stable", pe_ttm=7.84, roe_ttm_percent=18.90,
                      pb=1.4246, normalized_roe_percent=24.09,
                      listing_market="a", current_price=38.74,
                      historical_peak_pr=0.59, targets=[0.3, 0.4, 0.5, 0.8, 0.9, 1.0])
        tp = r["decision"]["target_price"]
        self.assertEqual(sorted(tp["buy"]), ["0.3", "0.4", "0.5"])
        self.assertEqual(sorted(tp["sell"]), ["norm_0.8", "norm_0.9", "norm_1.0"])
        self.assertEqual(len(tp["buy"]) + len(tp["sell"]), 6)


class PbGateTests(unittest.TestCase):
    def test_eight_pb_is_the_whole_rule(self):
        from calculate_valuation import pb_gate
        self.assertEqual(pb_gate(1.42)["status"], "clear")
        self.assertEqual(pb_gate(4.83)["status"], "clear")
        self.assertEqual(pb_gate(8.0)["status"], "clear")
        self.assertEqual(pb_gate(8.01)["status"], "blocked")
        self.assertEqual(pb_gate(45.15)["status"], "blocked")
        self.assertEqual(pb_gate(None)["status"], "pb_unknown")

    def test_blocked_means_no_new_position(self):
        from calculate_valuation import pb_gate
        self.assertEqual(pb_gate(23.02)["action"], "no_new_position")
        self.assertEqual(pb_gate(4.83)["action"], "proceed")


class BuyTierTests(unittest.TestCase):
    def test_normalized_can_veto_a_raw_pass(self):
        from calculate_valuation import buy_tier
        t = buy_tier(0.4613, 0.782)          # 格力
        self.assertIsNone(t["tier"])
        self.assertEqual(t["governed_by"], "normalized_position")

    def test_raw_can_veto_a_normalized_pass(self):
        from calculate_valuation import buy_tier
        t = buy_tier(0.62, 0.45)             # 历史一直很贵的股票
        self.assertIsNone(t["tier"])
        self.assertEqual(t["governed_by"], "raw_pr")

    def test_both_pass_takes_the_stricter_line(self):
        from calculate_valuation import buy_tier
        t = buy_tier(0.29, 0.39)
        self.assertEqual(t["tier"], "主要加仓")   # 0.39 卡住，不是 0.29 的深度价值
        self.assertEqual(t["governing_reading"], 0.39)


class PeakPrescreenTests(unittest.TestCase):
    def test_three_real_cases_all_skip(self):
        """格力／DECK／盐津铺子：粗筛应当一致判定"不用重建"。"""
        from calculate_valuation import peak_rebuild_needed
        for pe, roe, tag in [(25.6, 14.44, "格力"), (20.9, 12.56, "DECK"),
                             (127.6, 13.87, "盐津铺子")]:
            r = peak_rebuild_needed(max_historical_pe=pe,
                                    min_plausible_decision_roe_percent=roe)
            self.assertFalse(r["rebuild"], tag)
            self.assertGreaterEqual(r["lower_bound_peak_pr"], 1.0)

    def test_a_perennially_cheap_stock_still_needs_the_rebuild(self):
        """银行型：ROE 11%、历史最高 PE 只有 8 → 峰值PR 下界 0.73，会咬住。"""
        from calculate_valuation import peak_rebuild_needed
        r = peak_rebuild_needed(max_historical_pe=8.0,
                                min_plausible_decision_roe_percent=11.0)
        self.assertTrue(r["rebuild"])
        self.assertLess(r["lower_bound_peak_pr"], 1.0)

    def test_hk_market_line_raises_the_bar(self):
        """H股市场线 0.80 更低，同一只股票更容易需要重建。"""
        from calculate_valuation import peak_rebuild_needed
        r = peak_rebuild_needed(max_historical_pe=9.0,
                                min_plausible_decision_roe_percent=12.0, e_market=0.80)
        self.assertAlmostEqual(r["lower_bound_peak_pr"], 0.75)
        self.assertTrue(r["rebuild"])    # 0.75 < 0.80 → 峰值可能咬住
        a = peak_rebuild_needed(max_historical_pe=9.0,
                                min_plausible_decision_roe_percent=12.0, e_market=1.00)
        self.assertTrue(a["rebuild"])

    def test_missing_screen_inputs_fall_back_to_rebuilding(self):
        from calculate_valuation import peak_rebuild_needed
        r = peak_rebuild_needed(max_historical_pe=None,
                                min_plausible_decision_roe_percent=12.0)
        self.assertTrue(r["rebuild"])
        self.assertEqual(r["reason"], "insufficient_screen_inputs")


# 2026-09-18：这一行原本卡在文件中间，直接执行只收集到它之前定义的类，
# 后半段用例被静默跳过。交接文档里的回归命令用的正是直接执行。
if __name__ == "__main__":
    unittest.main()
