"""First bounded CPU fine-tuning run. Uses only supplementary public images."""
import hashlib,json,re,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
import torch,cv2,yaml
from ultralytics import YOLO
def prepare():
    source=DATA/'datasets'/'formula1-box'/'extracted';dest=DATA/'datasets'/'detector-prepared'
    files=list(source.glob('*/images/*'));seen=set();manifest=[]
    # Original source is one broadcast. Use chronological blocks and exclusion
    # gaps for a diagnostic split; do not call it independent-session validation.
    for p in sorted(files):
        label=p.parent.parent/'labels'/(p.stem+'.txt')
        if not label.exists():continue
        frame=int(re.search(r'frame_(\d+)',p.stem).group(1)) if re.search(r'frame_(\d+)',p.stem) else 0
        if 80000<=frame<85000:continue
        split='train' if frame<80000 else 'val'
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in seen:continue
        seen.add(digest)
        im=cv2.imread(str(p));small=cv2.resize(im,(16,16));phash=(cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)>small.mean()).flatten().tolist()
        target=dest/split/'images'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copy2(p,target)
        dst=dest/split/'labels'/(p.stem+'.txt');dst.parent.mkdir(exist_ok=True)
        rows=[]
        for row in label.read_text().splitlines():
            values=row.split()
            if len(values)==5:rows.append('0 '+' '.join(values[1:]))
            elif len(values)>=7 and len(values)%2==1:
                xs=list(map(float,values[1::2]));ys=list(map(float,values[2::2]));x1,x2=min(xs),max(xs);y1,y2=min(ys),max(ys)
                rows.append(f'0 {(x1+x2)/2} {(y1+y2)/2} {x2-x1} {y2-y1}')
        dst.write_text('\n'.join(rows))
        manifest.append(dict(path=str(target),original=str(p),sha256=digest,phash=phash,split=split,source_group='formula1-box-single-broadcast',frame=frame))
    dest.mkdir(exist_ok=True)
    for cache in dest.glob('*/labels.cache'):cache.unlink()
    assert sum(bool(p.read_text().strip()) for p in dest.glob('*/labels/*.txt'))>100, 'Insufficient nonempty labels'
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
    config=dict(path=str(dest),train='train/images',val='val/images',names={0:'formula_car'})
    (dest/'data.yaml').write_text(yaml.safe_dump(config))
    return dest,manifest
if __name__=='__main__':
    torch.set_num_threads(4)
    dest,manifest=prepare();print('Prepared',len(manifest),'images',flush=True)
    report={'status':'training','model':'YOLO11n','epochs':3,'image_size':320,'training_images':sum(x['split']=='train' for x in manifest),'validation_images':sum(x['split']=='val' for x in manifest),'split_limitation':'Same-broadcast chronological diagnostic split; independent-session validation unavailable','held_out_user_video':True,'tire_model':'pending reviewed tire labels','keypoint_model':'pending reviewed wheel labels','track_model':'pending reviewed segmentation labels','event_calibration':'not calibrated'}
    (DATA/'reports'/'evaluation.json').write_text(json.dumps(report,indent=2))
    model=YOLO('yolo11n.pt');shutil.copy2('yolo11n.pt',DATA/'models'/'yolo11n.pt')
    report['baseline_caveat']='Use class-agnostic IoU comparison; COCO class IDs differ from F1 dataset'
    model.train(data=str(dest/'data.yaml'),epochs=3,imgsz=320,batch=4,device='cpu',workers=0,cache=False,freeze=10,plots=False,project=str(DATA/'reports'),name='detector-training',exist_ok=True,seed=42,deterministic=True,amp=False)
    best=DATA/'reports'/'detector-training'/'weights'/'best.pt';shutil.copy2(best,DATA/'models'/'car-detector.pt')
    metrics=YOLO(str(best)).val(data=str(dest/'data.yaml'),imgsz=320,batch=4,device='cpu',workers=0,plots=False,project=str(DATA/'reports'),name='detector-eval',exist_ok=True)
    report.update(status='completed diagnostic training',metrics={k:float(v) for k,v in metrics.results_dict.items()},finished_at=time.time(),checkpoint_sha256=hashlib.sha256(best.read_bytes()).hexdigest())
    (DATA/'reports'/'evaluation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)
