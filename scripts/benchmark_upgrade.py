import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2,torch
from backend.store import ROOT,DATA,listing
from backend.perception import Perception,annotate
from backend.compute import compute_status
torch.set_num_threads(4)
asset=next(a for a in listing('asset') if 'Sao-Paulo' in a['name'])
cap=cv2.VideoCapture(asset['path']);cap.set(cv2.CAP_PROP_POS_FRAMES,1000);frames=[]
for _ in range(24):
 ok,im=cap.read()
 if ok:frames.append(im)
cap.release();report={'compute':compute_status(),'samples':len(frames),'resolution':[asset['width'],asset['height']],'timings':{}}
for device in ['cpu']+(['cuda:0'] if compute_status()['gpu_available'] else []):
 model=Perception(ROOT/'yolo11n-seg.pt',DATA/'models/wheel-segmenter.pt');model.device=device;model.compute=dict(model.compute,gpu_available=device!='cpu',device=device)
 model.frame(frames[0],999,asset['fps'],{})
 start=time.perf_counter();results=[]
 for i,im in enumerate(frames):results.append(model.frame(im,1000+i,asset['fps'],{}))
 if device!='cpu':torch.cuda.synchronize()
 elapsed=time.perf_counter()-start;report['timings'][device]={'seconds':elapsed,'fps':len(frames)/elapsed,'car_masks':sum(bool(c.get('mask')) for r in results for c in r['cars']),'track_paths':sum(len(r['track_lines']) for r in results)}
 cv2.imwrite(str(DATA/'reports'/('segmentation-'+device.replace(':','-')+'.jpg')),annotate(frames[-1].copy(),results[-1]))
 (DATA/'reports'/('segmentation-'+device.replace(':','-')+'.json')).write_text(json.dumps(results[-1],indent=2))
(DATA/'reports/gpu-benchmark.json').write_text(json.dumps(report,indent=2));print(report)
