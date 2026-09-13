import unittest
import numpy as np
from backend.perception import outside_track,Perception
from backend.simulation import simulate
def box(x,y):return [[x,y],[x+.05,y],[x+.05,y+.05],[x,y+.05]]
class AnalysisTests(unittest.TestCase):
 def test_all_four_outside(self):
  self.assertTrue(outside_track([[0,0],[1,0],[1,1],[0,1]],[box(2,i) for i in range(4)]))
 def test_touching_line_is_inside(self):
  self.assertFalse(outside_track([[0,0],[1,0],[1,1],[0,1]],[box(1,.5)]+[box(2,i) for i in range(3)]))
 def test_hidden_wheel_is_unknown(self):
  self.assertIsNone(outside_track([[0,0],[1,0],[1,1],[0,1]],[box(2,i) for i in range(3)]))
 def test_one_frame_flag_is_preserved(self):
  area=[[0,0],[1,0],[1,1],[0,1]]
  flags=[outside_track(area,[box(.5,.5)]*4),outside_track(area,[box(2,2)]*4),outside_track(area,[box(.5,.5)]*4)]
  self.assertEqual(flags,[False,True,False])
 def test_blank_frame_no_fabricated_confidence(self):
  r=Perception().frame(np.zeros((360,640,3),dtype=np.uint8),0,25,{})
  self.assertIsNone(r['confidence']);self.assertFalse(r['flagged'])
 def test_scenario_repeatability_and_nonnegative_speed(self):
  a=simulate();self.assertEqual(a,simulate());self.assertTrue(all(x['speed']>=0 for x in a['trajectory']))
if __name__=='__main__':unittest.main()
