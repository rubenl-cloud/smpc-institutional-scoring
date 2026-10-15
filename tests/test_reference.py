import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from reference import classify, flags, load_fixture
from prepare_experiment import prepare
from check_output import check


class ReferenceTests(unittest.TestCase):
    def test_below_equal_above_threshold(self):
        self.assertEqual(classify(149999, 1500000, 10), 0)
        self.assertEqual(classify(150000, 1500000, 10), 0)
        self.assertEqual(classify(150001, 1500000, 10), 1)

    def test_invalid_inputs(self):
        for args in [(-1, 100), (0, 0), (1, -2)]:
            with self.assertRaises(ValueError):
                classify(*args)

    def test_fixture_expected_flags(self):
        rows = load_fixture(ROOT / "data" / "synthetic.csv")
        self.assertEqual(flags(rows, 10), [1, 0, 0, 0])

    def test_generated_party_files_and_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            n, expected = prepare(ROOT / "data" / "synthetic.csv", base, 10)
            self.assertEqual(n, 4)
            self.assertEqual(expected.read_text().split(), ["1", "0", "0", "0"])
            self.assertEqual((base / "Player-Data" / "Input-P0-0").read_text().split(),
                             ["180000", "90000", "150000", "0"])
            self.assertEqual((base / "Player-Data" / "Input-P1-0").read_text().split(),
                             ["1500000", "1800000", "1500000", "2000000"])
            self.assertIn("THRESHOLD_PERCENT = 10", (base / "Programs" / "Source" / "energy_burden.mpc").read_text())

    def test_parse_output(self):
        check("Start\nRESULT 1\nRESULT 0\nRESULT 0\nRESULT 0\n", [1, 0, 0, 0])
        with self.assertRaises(AssertionError):
            check("RESULT 1\n", [0])


if __name__ == "__main__":
    unittest.main()
