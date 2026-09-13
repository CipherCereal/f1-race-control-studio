import unittest
import numpy as np
from backend.geometry import fit_ground_plane,project_trajectory
from backend.perception import Perception

class GeometryTests(unittest.TestCase):
 def test_known_projection(self):
  r=fit_ground_plane([[0,0],[10,0],[10,10],[0,10]],[[0,0],[1,0],[1,1],[0,1]])
  p=project_trajectory(r['matrix'],[dict(x=5,y=5,time=0)])[0]['point']
  np.testing.assert_allclose(p,[.5,.5],atol=1e-6)
 def test_collinear_rejected(self):
  with self.assertRaises(ValueError):fit_ground_plane([[0,0],[1,0],[2,0],[3,0]],[[0,0],[1,0],[1,1],[0,1]])
 def test_manual_geometry_does_not_invent_score(self):
  area=[[0,0],[.1,0],[.1,.1],[0,.1]]
  contact=[[.5,.5],[.6,.5],[.6,.6],[.5,.6]]
  r=Perception().frame(np.zeros((360,640,3),dtype=np.uint8),0,25,dict(polygon=area,contacts=[contact]*4))
  self.assertTrue(r['flagged']);self.assertIsNone(r['confidence'])
