"""Experimental wheel segmentation on road-car parts, not F1 validation."""
import sys,json,zipfile,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
from scripts.acquire import usage,LIMIT
import torch,yaml
from ultralytics import YOLO
def main():
 torch.set_num_threads(4);folder=DATA/'datasets'/'carparts';target=folder/'extracted';target.mkdir(exist_ok=True)
 with zipfile.ZipFile(folder/'source.zip') as z:
  if usage()+sum(i.file_size for i in z.infolist())>LIMIT:raise RuntimeError('Dataset budget exceeded')
  for i in z.infolist():
   dst=(target/i.filename).resolve()
   if not dst.is_relative_to(target.resolve()):raise RuntimeError('Unsafe archive member')
   if not dst.exists():z.extract(i,target)
 source=next(p for p in target.rglob('images') if p.is_dir());dest=folder/'wheel-training';manifest=[]
 for split,limit in [('train',320),('val',80)]:
  paths=sorted((source/split).glob('*'));count=0
  for p in paths:
   lab=source.parent/'labels'/split/(p.stem+'.txt')
   if not lab.exists():continue
   labels=['0 '+' '.join(line.split()[1:]) for line in lab.read_text().splitlines() if line.split() and line.split()[0]=='22']
   if not labels:continue
   dst=dest/'images'/split/p.name;dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists():shutil.copy2(p,dst)
   label=dest/'labels'/split/(p.stem+'.txt');label.parent.mkdir(parents=True,exist_ok=True);label.write_text('\n'.join(labels))
   manifest.append(dict(path=str(dst),source=str(p),split=split,sha256=hashlib.sha256(p.read_bytes()).hexdigest()));count+=1
   if count>=limit:break
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2));(dest/'data.yaml').write_text(yaml.safe_dump(dict(path=str(dest),train='images/train',val='images/val',names={0:'wheel'})))
 model=YOLO('yolo11n-seg.pt');model.train(data=str(dest/'data.yaml'),epochs=3,imgsz=320,batch=4,device='cpu',workers=0,freeze=10,plots=False,project=str(DATA/'reports'),name='wheel-training',exist_ok=True,amp=False,seed=42)
 best=DATA/'reports'/'wheel-training'/'weights'/'best.pt';shutil.copy2(best,DATA/'models'/'wheel-segmenter.pt')
 metrics=YOLO(str(best)).val(data=str(dest/'data.yaml'),imgsz=320,batch=4,device='cpu',workers=0,plots=False,project=str(DATA/'reports'),name='wheel-eval',exist_ok=True)
 report=dict(status='experimental road-car training complete',metrics={k:float(v) for k,v in metrics.results_dict.items()},train_images=sum(x['split']=='train' for x in manifest),validation_images=sum(x['split']=='val' for x in manifest),scope='road-car wheels; F1 generalization unvalidated',contact_points='mask bottom is a proxy, not measured road contact',checkpoint_sha256=hashlib.sha256(best.read_bytes()).hexdigest())
 (DATA/'reports'/'wheel-evaluation.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
