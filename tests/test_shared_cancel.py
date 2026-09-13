import tempfile,unittest,threading
from pathlib import Path
from unittest.mock import patch
from backend import main,jobs

class SharedCancelTests(unittest.TestCase):
 def test_other_worker_request_is_persisted_and_forwarded(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'analyses').mkdir()
   with patch.object(main,'DATA',root),patch.object(main,'safe_get',return_value={'status':'running'}),patch('requests.post') as post:
    self.assertEqual(main.cancel('test')['status'],'cancellation requested')
    self.assertTrue((root/'analyses/test/cancel.request').exists())
    post.assert_called_once()
 def test_shared_marker_cancels_waiting_job(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'analyses/test';p.mkdir(parents=True);(p/'cancel.request').touch()
   j={'id':'test','status':'queued'}
   with patch.object(jobs,'DATA',root),patch.dict(jobs.CANCEL,{'test':threading.Event()}),patch.object(jobs,'run') as run,patch.object(jobs,'put'):
    jobs.queued_run(j,{})
    self.assertEqual(j['status'],'cancelled');run.assert_not_called()
