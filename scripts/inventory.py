"""Snapshot acquired files and checkpoint identity without rewriting training splits."""
import hashlib,json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(4*1024*1024):h.update(chunk)
 return h.hexdigest()
def main():
 root=DATA/'datasets';manifest=DATA/'acquired-files.jsonl';total=0;count=0
 with manifest.open('w') as f:
  for p in root.rglob('*'):
   if not p.is_file() or p.suffix=='.part':continue
   size=p.stat().st_size;total+=size;count+=1
   f.write(json.dumps(dict(path=str(p.relative_to(root)),bytes=size,sha256=sha(p),usage='acquired; consult split manifests before training'))+'\n')
 summary=dict(snapshot_at=time.time(),files=count,bytes=total,budget_bytes=50_000_000_000,within_budget=total<=50_000_000_000,held_out_video_included=False)
 (DATA/'reports'/'inventory.json').write_text(json.dumps(summary,indent=2))
 (DATA/'reports'/'checkpoint-manifest.json').write_text(json.dumps([dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),role='pretrained baseline' if p.name=='yolo11n.pt' else 'trained diagnostic model') for p in (DATA/'models').glob('*.pt')],indent=2))
 print(summary)
if __name__=='__main__':main()
