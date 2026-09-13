import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import acquire
class Response:
 headers={}
 def raise_for_status(self):pass
 def iter_content(self,size):yield b'123456';yield b'123456'
class AcquisitionTests(unittest.TestCase):
 def test_unknown_size_stream_cannot_exceed_budget(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with patch.object(acquire,'BASE',root),patch.object(acquire,'LIMIT',10),patch.object(acquire,'_download_bytes',None),patch.object(acquire.requests,'get',return_value=Response()):
    with self.assertRaises(RuntimeError):acquire.download('https://example.invalid',root/'sample.bin')
    self.assertLessEqual(sum(p.stat().st_size for p in root.iterdir()),10)
    self.assertFalse((root/'sample.bin').exists())
