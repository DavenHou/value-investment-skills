#!/usr/bin/env python3

import unittest

from calculate_valuation import calculate


class CalculateValuationTests(unittest.TestCase):
    def test_aligned_ttm_snapshot(self):
        result = calculate(pe_ttm=14.7, roe_ttm_percent=31, current_price=100)
        self.assertEqual(result["calculation_basis"], "aligned_ttm")
        self.assertAlmostEqual(result["base_pr"]["from_pe_ttm"], 14.7 / 31)
        self.assertIn("0.55", result["target_map"])

    def test_rejects_half_ttm_pair(self):
        with self.assertRaisesRegex(ValueError, "must be provided together"):
            calculate(pe_ttm=14.7, roe_percent=31)

    def test_normalized_pb_path_remains_available(self):
        result = calculate(pb=0.96, roe_percent=15.88, listing_market="hk")
        self.assertEqual(result["calculation_basis"], "normalized_or_unspecified_period")
        self.assertAlmostEqual(result["base_pr"]["from_pb"], 100 * 0.96 / 15.88**2)
        self.assertIn("0.44", result["target_map"])


if __name__ == "__main__":
    unittest.main()
