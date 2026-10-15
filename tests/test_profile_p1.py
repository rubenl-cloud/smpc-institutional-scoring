from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from check_profile_p1 import check, parse_results
from prepare_profile_p1 import prepare
from profile_p1_reference import evaluate_profile, expected_results, load_parties


class ProfileP1Tests(unittest.TestCase):
    def test_activation_and_weighted_scores(self):
        results = expected_results(load_parties())
        self.assertEqual([result.active for result in results], [1, 1, 0, 1, 0, 1, 1])
        self.assertEqual([result.score for result in results], [100, 40, 0, 85, 0, 100, 55])

    def test_strict_burden_boundary_and_linear_weights(self):
        at_threshold = evaluate_profile(1_000_000, 75_000, 25_000, 1)
        self.assertEqual((at_threshold.active, at_threshold.score), (0, 0))
        structural = evaluate_profile(800_000, 75_000, 25_001, 0)
        self.assertEqual(structural.to_dict(), {
            "active": 1, "score": 85, "i2_relative_poverty": 1,
            "i3_high_energy_burden": 1, "i4_payment_incident": 0,
        })
        burden_only = evaluate_profile(1_500_000, 150_001, 0, 0)
        self.assertEqual((burden_only.active, burden_only.score), (1, 40))

    def test_bad_data_and_weights(self):
        for args in ((0, 100, 100, 0), (1, -1, 0, 0), (1, 0, 0, 2)):
            with self.assertRaises(ValueError):
                evaluate_profile(*args)
        with self.assertRaises(ValueError):
            evaluate_profile(1, 0, 0, 0, weight_i2=1, weight_i3=1, weight_i4=1)

    def test_prepare_uses_owner_separated_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            count, expected, source = prepare(root, ROOT / "data", program_name="profile_p1_test")
            self.assertEqual(count, 7)
            self.assertEqual(expected.read_text().splitlines()[0], "1 100")
            self.assertEqual((root / "inputs" / "Input-P0-0").read_text().split()[0], "900000")
            self.assertEqual((root / "inputs" / "Input-P1-0").read_text().split()[:2], ["90000", "1"])
            self.assertEqual((root / "inputs" / "Input-P2-0").read_text().split()[0], "35000")
            self.assertIn("P1_SCORE", source.read_text())

    def test_mpc_output_verification(self):
        transcript = "start\nP1_ACTIVE 1 P1_SCORE 100\nP1_ACTIVE 0 P1_SCORE 0\n"
        self.assertEqual(parse_results(transcript), [(1, 100), (0, 0)])
        check(transcript, [(1, 100), (0, 0)])
        with self.assertRaises(AssertionError):
            check("P1_ACTIVE 1 P1_SCORE 40\n", [(1, 100)])


if __name__ == "__main__":
    unittest.main()
