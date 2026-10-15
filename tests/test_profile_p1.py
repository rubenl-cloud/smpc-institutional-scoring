from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from profile_p1_reference import classify, load_parties, expected_tiers
from prepare_profile_p1 import prepare
from check_profile_p1 import check


class ProfileP1Tests(unittest.TestCase):
    def test_activation_three_sources(self):
        self.assertEqual(expected_tiers(load_parties()), [2, 0, 0, 1, 0, 2, 0])

    def test_boundaries_and_reinforcement(self):
        self.assertEqual(classify(1_050_000, 80_000, 25_000, 1), 0)
        self.assertEqual(classify(1_080_000, 120_000, 0, 1), 0)
        self.assertEqual(classify(800_000, 75_000, 25_000, 0), 1)
        self.assertEqual(classify(900_000, 90_000, 35_000, 1), 2)
        self.assertEqual(classify(900_000, 90_000, 35_000, 0), 1)

    def test_bad_data(self):
        for args in ((0, 100, 100, 0), (1, -1, 0, 0), (1, 0, 0, 2)):
            with self.assertRaises(ValueError):
                classify(*args)

    def test_prepare_party_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            count, expected = prepare(root, ROOT / 'data')
            self.assertEqual(count, 7)
            self.assertEqual(expected.read_text().split(), ['2', '0', '0', '1', '0', '2', '0'])
            self.assertEqual((root / 'Player-Data' / 'Input-P0-0').read_text().split()[0], '900000')
            self.assertEqual((root / 'Player-Data' / 'Input-P1-0').read_text().split()[:2], ['90000', '1'])
            self.assertEqual((root / 'Player-Data' / 'Input-P2-0').read_text().split()[0], '35000')
            source = (root / 'Programs' / 'Source' / 'profile_p1.mpc').read_text()
            self.assertIn('sint.get_input_from(2)', source)
            self.assertIn('P1_TIER', source)

    def test_mpc_output_verification(self):
        check('start\nP1_TIER 2\nP1_TIER 0\nP1_TIER 0\nP1_TIER 1\nP1_TIER 0\nP1_TIER 2\nP1_TIER 0\n', [2, 0, 0, 1, 0, 2, 0])
        with self.assertRaises(AssertionError):
            check('P1_TIER 1\n', [2])


if __name__ == '__main__':
    unittest.main()
