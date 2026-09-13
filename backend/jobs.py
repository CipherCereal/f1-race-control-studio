import csv,json,threading,time,traceback,os
from pathlib import Path
import cv2
from .store import DATA,put,get
from .perception import Perception,annotate
CANCEL={}
SUBMIT_LOCK=threading.RLock()
WORKER_LOCK=threading.Lock()

def reconcile_workers():
    import psutil
    from .store import listing
    for job in listing('job'):
        if job['status'] not in ('running','queued') or not job.get('worker_pid'):continue
        try:alive=abs(psutil.Process(job['worker_pid']).create_time()-job['worker_started'])<1
        except (psutil.NoSuchProcess,psutil.AccessDenied):alive=False
        if not alive:
            job.update(status='interrupted',error='Analysis worker stopped. Restart to reconstruct tracking consistently.');put('job',job)

def queued_run(job,asset):
    with WORKER_LOCK:
        if CANCEL[job['id']].is_set() or (DATA/'analyses'/job['id']/'cancel.request').exists():
            job['status']='cancelled';put('job',job);return
        run(job,asset)

def submit(asset,mode='preview',calibration=None):
    from .store import listing
    with SUBMIT_LOCK:
        for job in listing('job'):
            if job['asset_id']==asset['id'] and job['mode']==mode and job.get('calibration',{})==(calibration or {}) and job['status'] in ('queued','running'):
                return job
        return start(asset,mode,calibration)
def start(asset,mode='preview',calibration=None,resume=None):
    job=resume or put('job',dict(asset_id=asset['id'],status='queued',mode=mode,processed=0,total=asset['frames'],calibration=calibration or {},schema_version=1))
    import psutil
    job.update(status='queued',worker_pid=os.getpid(),worker_started=psutil.Process().create_time(),error=None);put('job',job)
    CANCEL[job['id']]=threading.Event()
    (DATA/'analyses'/job['id']/'cancel.request').unlink(missing_ok=True)
    threading.Thread(target=queued_run,args=(job,asset),daemon=True).start()
    return job
def run(job,asset):
    cap=None;writer=None
    try:
        folder=DATA/'analyses'/job['id'];folder.mkdir(exist_ok=True)
        weights=DATA/'models'/'car-segmenter.pt'
        if not weights.exists():weights=DATA.parent/'yolo11n-seg.pt'
        wheel_weights=DATA/'models'/'wheel-segmenter.pt'
        model=Perception(weights if weights.exists() else None,wheel_weights if wheel_weights.exists() else None)
        cap=cv2.VideoCapture(asset['path']);fps=asset['fps'];stride=1 if job['mode']=='final' else max(1,round(fps))
        stop=asset['frames'] if job['mode']=='final' else min(asset['frames'],round(60*fps))
        # Resume reruns from source to reconstruct tracking state consistently.
        job.update(status='running',processed=0,error=None,model=str(weights) if weights.exists() else 'classical CV only',started_at=time.time());put('job',job)
        writer=cv2.VideoWriter(str(folder/'annotated.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps/stride,(asset['width'],asset['height']))
        events=[];idx=0;written=0;pending=[]
        (folder/'events.json').write_text('[]')
        batch_size=4 if model.compute['gpu_available'] and model.model and stride==1 else 1
        from .frame_index import invalidate
        invalidate(folder/'frames.jsonl')
        with (folder/'frames.jsonl').open('w') as out:
            while idx<stop:
                if CANCEL[job['id']].is_set() or (folder/'cancel.request').exists():job['status']='cancelled';break
                if not pending:
                    for _ in range(min(batch_size,stop-idx)):
                        ok,decoded=cap.read()
                        if not ok:break
                        pending.append((decoded,cap.get(cv2.CAP_PROP_POS_MSEC)/1000))
                    if pending and batch_size>1:model.preload([p[0] for p in pending],idx)
                if not pending:
                    job['decode_gap']=dict(expected=stop,decoded=idx);break
                frame,timestamp=pending.pop(0)
                if idx%stride==0:
                    r=model.frame(frame,idx,fps,job['calibration'])
                    r['time']=timestamp if timestamp>0 or idx==0 else idx/fps
                    r['timestamp_source']='decoder PTS' if timestamp>0 or idx==0 else 'estimated frame/fps'
                    out.write(json.dumps(r)+'\n');written+=1
                    out.flush()
                    if r['flagged']:
                        events.append(dict(frame=idx,time=r['time'],type='track limits',confidence=r['confidence'],evidence=r['evidence']))
                        # Publish alerts during processing, not only at job completion.
                        event_temp=folder/'events.pending.json'
                        event_temp.write_text(json.dumps(events))
                        event_temp.replace(folder/'events.json')
                    writer.write(annotate(frame.copy(),r))
                    if written==1:cv2.imwrite(str(folder/'first-frame.jpg'),annotate(frame.copy(),r))
                idx+=1
                if idx%25==0:job.update(processed=idx,analyzed_frames=written,events=len(events));put('job',job)
        (folder/'events.json').write_text(json.dumps(events,indent=2))
        with (folder/'events.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['frame','time','type','confidence','evidence']);w.writeheader();w.writerows(events)
        if job['status']!='cancelled':job['status']='complete' if idx==stop else 'incomplete'
        job.update(processed=idx,analyzed_frames=written,events=len(events),finished_at=time.time(),stride=stride,output=str(folder))
        import hashlib
        from .store import ROOT
        checkpoints={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [weights,wheel_weights,ROOT/'yolo11s-seg.pt'] if p.exists()}
        manifest=dict(schema_version=2,job=job,asset=asset,checkpoints=checkpoints,limitations=['No calibrated probability','Painted-line candidates are not validated track boundaries','No physical speed without calibration','Hidden wheels require geometry','Wheel masks trained on road cars; F1 performance unvalidated','No trained track-segmentation or wheel-contact-keypoint checkpoint'],ghost_mode='none',ego_path='recorded fixed',reproducibility='input, checkpoint hashes and configuration recorded; empirical repeatability pending')
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2));put('job',job)
    except Exception as e:job.update(status='failed',error=str(e),trace=traceback.format_exc());put('job',job)
    finally:
        if cap:cap.release()
        if writer:writer.release()
