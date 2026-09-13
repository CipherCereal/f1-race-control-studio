import unittest,threading
from unittest.mock import patch
from backend import jobs

class SubmissionTests(unittest.TestCase):
 def test_duplicate_returns_existing_job(self):
  existing=dict(id='existing',asset_id='a',mode='final',calibration={},status='running')
  with patch('backend.store.listing',return_value=[existing]),patch.object(jobs,'start') as start:
   self.assertEqual(jobs.submit({'id':'a'},'final'),existing)
   start.assert_not_called()
 def test_other_video_is_accepted(self):
  existing=dict(id='existing',asset_id='a',mode='final',calibration={},status='running')
  with patch('backend.store.listing',return_value=[existing]),patch.object(jobs,'start',return_value={'id':'new'}) as start:
   self.assertEqual(jobs.submit({'id':'b'},'final'),{'id':'new'})
   start.assert_called_once()
 def test_cancelled_queue_never_runs(self):
  event=threading.Event();event.set();j={'id':'queued','status':'queued'}
  with patch.dict(jobs.CANCEL,{'queued':event}),patch.object(jobs,'run') as run,patch.object(jobs,'put'):
   jobs.queued_run(j,{})
   run.assert_not_called();self.assertEqual(j['status'],'cancelled')
