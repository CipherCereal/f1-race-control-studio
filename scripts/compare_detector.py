"""Same images and class-agnostic IoU matching for COCO and fine-tuned model."""
import sys,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
import numpy as np,torch
from ultralytics import YOLO
def iou(a,b):
 inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]));union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
 return inter/max(union,1e-9)
def main():
 torch.set_num_threads(4);paths=sorted((DATA/'datasets'/'detector-prepared'/'val'/'images').glob('*'));results={}
 for name in ['yolo11n.pt','car-detector.pt']:
  model=YOLO(str(DATA/'models'/name));tp=fp=fn=0;scores=[];labels=[]
  for p in paths:
   truth=[]
   for line in (p.parent.parent/'labels'/(p.stem+'.txt')).read_text().splitlines():
    _,x,y,w,h=map(float,line.split());truth.append([x-w/2,y-h/2,x+w/2,y+h/2])
   pred=model.predict(str(p),imgsz=320,conf=.25,device='cpu',verbose=False)[0];matched=set()
   for box in pred.boxes:
    if name=='yolo11n.pt' and int(box.cls[0]) not in [2,5,7]:continue
    b=box.xyxyn[0].tolist();candidates=[(iou(b,t),i) for i,t in enumerate(truth) if i not in matched];best=max(candidates,default=(0,-1));hit=best[0]>=.5
    if hit:tp+=1;matched.add(best[1])
    else:fp+=1
    scores.append(float(box.conf[0]));labels.append(int(hit))
   fn+=len(truth)-len(matched)
  results[name]=dict(images=len(paths),tp=tp,fp=fp,fn=fn,precision=tp/max(1,tp+fp),recall=tp/max(1,tp+fn),brier_detection_score=float(np.mean((np.array(scores)-labels)**2)) if scores else None,confidence_threshold=.25,iou_threshold=.5)
 report=dict(results=results,scope='same-broadcast chronological diagnostic validation',calibration='Brier score diagnostic only; no calibrated event probabilities',held_out_user_video_used=False)
 (DATA/'reports'/'baseline-comparison.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
