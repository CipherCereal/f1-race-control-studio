import unittest,cv2,numpy as np
from backend.track_lines import TrackLines
class Endpoints(unittest.TestCase):
 def test_endpoints_follow_paint(self):
  tracker=TrackLines();results=[]
  for i,(top,bottom) in enumerate([(160,400),(190,430)]):
   frame=np.full((540,960,3),80,np.uint8)
   cv2.line(frame,(420,top),(200,bottom),(255,255,255),5)
   lines=tracker.update(frame,i,25)
   self.assertTrue(lines);self.assertTrue(all(x['side']=='left' for x in lines))
   results.append(lines[0]['points'])
  self.assertGreater(results[1][0][1],results[0][0][1]+.02)
  self.assertGreater(results[1][-1][1],results[0][-1][1]+.02)
