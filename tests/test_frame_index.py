import json,tempfile,unittest
from pathlib import Path
from backend.frame_index import read_frame
class FrameIndexTests(unittest.TestCase):
 def test_no_nearest_frame_substitution_and_live_append(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'frames.jsonl';p.write_text(json.dumps({'frame':0})+'\n')
   self.assertEqual(read_frame(p,0)['frame'],0)
   self.assertEqual(read_frame(p,1)['track_limit'],'frame not analyzed')
   with p.open('a') as f:f.write(json.dumps({'frame':25})+'\n')
   self.assertEqual(read_frame(p,25)['frame'],25)
