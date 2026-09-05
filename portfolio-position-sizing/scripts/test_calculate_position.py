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

    def test_current_policy_defaults(self):
        completed = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--risk-budget-percent", "100",
                "--stress-loss-low-percent", "40", "--stress-loss-high-percent", "60",
            ], check=True, text=True, capture_output=True
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["inputs"]["preferred_stock_count_low"], 5)
        self.assertEqual(result["inputs"]["preferred_stock_count_high"], 8)
        self.assertIn("single_name", result["binding_constraint"])


if __name__ == "__main__":
    unittest.main()
