import unittest,cv2,numpy as np
from backend.track_lines import TrackLines
class TrackLineTests(unittest.TestCase):
 def test_far_paint_is_not_cropped(self):
  image=np.full((540,960,3),80,np.uint8)
  cv2.line(image,(420,145),(210,420),(255,255,255),5)
  cv2.line(image,(540,145),(750,420),(255,255,255),5)
  paths=TrackLines().update(image,0,25)
  self.assertEqual(len(paths),2)
  self.assertTrue(all(min(p[1] for p in line['points'])<.30 for line in paths))
 def test_blank_does_not_invent_circuit(self):
  self.assertEqual(TrackLines().update(np.zeros((360,640,3),np.uint8),0,25),[])
 def test_inferred_paths_expire_and_cut_resets(self):
  t=TrackLines();t.previous={'left':dict(points=np.array([[.2,.4],[.1,.8]]),observed_frame=0)}
  image=np.zeros((360,640,3),np.uint8)
  self.assertIn('inferred',t.update(image,1,25)[0]['kind'])
  self.assertEqual(t.update(image,20,25),[])
  self.assertEqual(t.update(image,1,25,cut=True),[])
 def test_prior_is_labeled_inferred(self):
  r=TrackLines().update(np.zeros((360,640,3),np.uint8),0,25,prior=[[.1,.1],[.2,.2]])
  self.assertEqual(r[0]['kind'],'inferred analyst circuit geometry');self.assertIsNone(r[0]['confidence'])
