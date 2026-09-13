"""Extend held-out fingerprint screening to every actual training snapshot."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA,ROOT
from scripts.audit_data import dhash
import cv2
paths=[DATA/'datasets/detector-prepared/manifest.json',DATA/'datasets/steering/split-manifest.json',DATA/'datasets/carparts/wheel-training/manifest.json']
samples=[]
for path in paths:
 for row in json.loads(path.read_text()):
  im=cv2.imread(row['path'])
  if im is not None:samples.append((row['path'],int(dhash(im),16),str(path),row['split']))
matches=[];cap=cv2.VideoCapture(str(ROOT.parent/'videoplayback (1).mp4'));count=0
while True:
 ok,im=cap.read()
 if not ok:break
 h=int(dhash(im),16)
 for path,value,manifest,split in samples:
  distance=(h^value).bit_count()
  if distance<=3:matches.append(dict(frame=count,path=path,hamming_distance=distance,manifest=manifest,split=split))
 count+=1
cap.release()
report=dict(checked_at=time.time(),heldout_frames=count,snapshot_images=len(samples),manifests=[str(p) for p in paths],candidates=matches,method='64-bit difference hash, Hamming <=3; candidate review required; transformed or cropped duplicates may be missed',scope='Actual training/validation snapshots only; subsequent downloads were not used for training')
(DATA/'reports/heldout-leakage.json').write_text(json.dumps(report,indent=2));print({'frames':count,'samples':len(samples),'candidates':len(matches)})
