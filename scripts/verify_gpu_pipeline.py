"""Held-out 77-frame integration check, including a partial GPU batch."""
import sys, threading, json,uuid,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from backend.store import DATA, listing, put
from backend.main import asset
from backend.jobs import run, CANCEL
source=next(a for a in listing('asset') if 'Sao-Paulo' in a['name'])
path=DATA/'uploads'/('gpu-validation-'+uuid.uuid4().hex+'.mp4')
cap=cv2.VideoCapture(source['path']);cap.set(cv2.CAP_PROP_POS_FRAMES,1000)
writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),source['fps'],(source['width'],source['height']))
for i in range(77):
    ok,frame=cap.read();assert ok
    writer.write(frame)
cap.release();writer.release()
import imageio_ffmpeg
browser_path=path.with_name(path.stem+'-browser.mp4')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-i',str(path),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(browser_path)],check=True,capture_output=True)
path=browser_path
a=asset(path,True);a.update(parent_asset_id=source['id'],parent_start_frame=1000,purpose='held-out GPU integration validation');put('asset',a)
j=put('job',dict(asset_id=a['id'],status='queued',mode='final',processed=0,total=77,calibration={},schema_version=1))
CANCEL[j['id']]=threading.Event();run(j,a)
assert j['status']=='complete',j
rows=[json.loads(line) for line in (DATA/'analyses'/j['id']/'frames.jsonl').read_text().splitlines()]
assert [r['frame'] for r in rows]==list(range(77))
assert all(rows[i]['time']<rows[i+1]['time'] for i in range(76))
assert all(r['compute']['gpu_available'] for r in rows)
report=dict(job_id=j['id'],frames=len(rows),contours=sum(bool(c.get('mask')) for r in rows for c in r['cars']),compute=rows[0]['compute'],source_asset_id=source['id'],source_start_frame=1000,held_out=True,status='passed',scope='decode, CUDA batch inference including partial batch, frame ordering, timestamps, annotation and export; accuracy not evaluated')
(DATA/'reports'/'gpu-pipeline-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
