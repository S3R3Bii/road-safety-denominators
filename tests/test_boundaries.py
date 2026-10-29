import sys,unittest
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from accounting import feasible,ceil

class RoundingBoundaries(unittest.TestCase):
    def test_closed_tie_endpoints(self):self.assertEqual(feasible(200,{'x':1})['x'],(1,3))
    def test_zero_share_can_hide_fatality(self):self.assertEqual(feasible(1000,{'x':0})['x'],(0,5))
    def test_hundred_share(self):self.assertEqual(feasible(200,{'x':100})['x'],(199,200))
    def test_tighten_upper_by_other_classes(self):self.assertEqual(feasible(200,{'x':50,'y':51})['x'],(99,99))
    def test_impossible_small_percentage(self):
        with self.assertRaisesRegex(AssertionError,'Empty'):feasible(1,{'x':50})
    def test_infeasible_partition(self):
        with self.assertRaisesRegex(AssertionError,'cannot fit'):feasible(100,{'x':80,'y':80})
    def test_ceil_negative_and_fraction(self):self.assertEqual([ceil(Fraction(x,2)) for x in [-3,-1,1,3]],[-1,0,1,2])

if __name__=='__main__':unittest.main()
