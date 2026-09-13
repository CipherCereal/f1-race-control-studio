import unittest,psutil
from unittest.mock import patch
from backend.jobs import reconcile_workers
class WorkerLiveness(unittest.TestCase):
 def test_dead_worker_is_interrupted(self):
  j=dict(status='running',worker_pid=99,worker_started=1)
  with patch('backend.store.listing',return_value=[j]),patch('psutil.Process',side_effect=psutil.NoSuchProcess(99)),patch('backend.jobs.put'):
   reconcile_workers();self.assertEqual(j['status'],'interrupted')
 def test_live_worker_preserved(self):
  j=dict(status='running',worker_pid=99,worker_started=1)
  with patch('backend.store.listing',return_value=[j]),patch('psutil.Process') as process,patch('backend.jobs.put') as put:
   process.return_value.create_time.return_value=1
   reconcile_workers();put.assert_not_called()
