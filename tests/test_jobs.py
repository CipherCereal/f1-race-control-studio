import json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
import cv2,numpy as np
from backend import jobs
from backend.perception import Perception

class JobTests(unittest.TestCase):
 def test_cancel_restart_and_single_frame_export(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'analyses').mkdir();(root/'models').mkdir()
   source=root/'source.avi';writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),5,(64,64))
   self.assertTrue(writer.isOpened())
   for _ in range(10):writer.write(np.zeros((64,64,3),dtype=np.uint8))
   writer.release()
   area=[[0,0],[.1,0],[.1,.1],[0,.1]];contact=[[.5,.5],[.6,.5],[.6,.6],[.5,.6]]
   job=dict(id='test',mode='final',status='queued',calibration=dict(polygon=area,contacts=[contact]*4,start_frame=5,end_frame=5))
   asset=dict(path=str(source),fps=5,frames=10,width=64,height=64)
   jobs.CANCEL['test']=threading.Event()
   class Cancellable(Perception):
    def frame(self,frame,idx,fps,calibration):
     result=super().frame(frame,idx,fps,calibration)
     if idx==3:jobs.CANCEL['test'].set()
     return result
   with patch.object(jobs,'DATA',root),patch.object(jobs,'put',lambda kind,value:value),patch.object(jobs,'Perception',Cancellable):
    jobs.run(job,asset)
   self.assertEqual(job['status'],'cancelled');self.assertEqual(job['processed'],4)
   jobs.CANCEL['test'].clear()
   class Observing(Perception):
    def frame(self,frame,idx,fps,calibration):
     if idx==6:
      published=json.loads((root/'analyses/test/events.json').read_text())
      self_test.assertEqual([e['frame'] for e in published],[5])
     return super().frame(frame,idx,fps,calibration)
   self_test=self
   with patch.object(jobs,'DATA',root),patch.object(jobs,'put',lambda kind,value:value),patch.object(jobs,'Perception',Observing):jobs.run(job,asset)
   self.assertEqual(job['status'],'complete')
   rows=[json.loads(x) for x in (root/'analyses/test/frames.jsonl').read_text().splitlines()]
   self.assertEqual([r['frame'] for r in rows],list(range(10)))
   events=json.loads((root/'analyses/test/events.json').read_text())
   self.assertEqual([e['frame'] for e in events],[5]);self.assertIsNone(events[0]['confidence'])
   jobs.CANCEL.pop('test',None)
