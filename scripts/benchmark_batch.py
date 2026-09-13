import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2,torch
from backend.store import ROOT,DATA,listing
from backend.perception import Perception
torch.set_num_threads(4)
a=next(a for a in listing('asset') if 'Sao-Paulo' in a['name']);cap=cv2.VideoCapture(a['path']);cap.set(1,1000);frames=[]
for _ in range(24):
 ok,im=cap.read()
 if ok:frames.append(im)
cap.release();m=Perception(ROOT/'yolo11n-seg.pt',DATA/'models/wheel-segmenter.pt');m.preload(frames[:8],992)
for i,im in enumerate(frames[:8]):m.frame(im,992+i,a['fps'],{})
torch.cuda.synchronize();start=time.perf_counter()
for start_idx in range(0,24,8):
 chunk=frames[start_idx:start_idx+8];m.preload(chunk,1000+start_idx)
 for j,im in enumerate(chunk):m.frame(im,1000+start_idx+j,a['fps'],{})
torch.cuda.synchronize();elapsed=time.perf_counter()-start
p=DATA/'reports/gpu-benchmark.json';r=json.loads(p.read_text());r['timings']['cuda_batch8']=dict(seconds=elapsed,fps=24/elapsed,batch_size=8);p.write_text(json.dumps(r,indent=2));print(r['timings'])
