import unittest,cv2,numpy as np
from backend.track_cues import track_cues
from backend.perception import plausible_mask,distinct_masks

class CueTests(unittest.TestCase):
 def test_duplicate_masks_suppressed(self):
  p=[[.2,.5],[.8,.5],[.8,.9],[.2,.9]]
  self.assertEqual(len(distinct_masks([dict(mask=p,score=.8),dict(mask=p,score=.4)])),1)
 def test_full_screen_mask_rejected(self):
  self.assertFalse(plausible_mask([[0,0],[1,0],[1,1],[0,1]]))
  self.assertTrue(plausible_mask([[.2,.5],[.8,.5],[.8,1],[.2,1]]))
 def test_horizontal_distant_paint(self):
  frame=np.full((540,960,3),80,np.uint8)
  cv2.line(frame,(100,90),(800,110),(255,255,255),4)
  paths=track_cues(frame)
  self.assertTrue(any(max(p[1] for p in c['points'])<.25 for c in paths))
 def test_curbs_separate_from_legal_boundary(self):
  frame=np.full((540,960,3),80,np.uint8)
  for i in range(10):cv2.rectangle(frame,(100+i*20,200),(120+i*20,214),(0,0,255) if i%2 else (255,255,255),-1)
  curbs=[c for c in track_cues(frame) if c['cue']=='red-white curb']
  self.assertTrue(curbs);self.assertTrue(all(c['legal_boundary'] is False for c in curbs))
