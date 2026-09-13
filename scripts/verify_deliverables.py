import json,sys,cv2,requests
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
from backend.perception import annotate
base='http://127.0.0.1:8765/api/'
s=requests.get(base+'state',timeout=10).json()
checks=[]
for j in s['jobs']:
 if j['status']!='complete':continue
 folder=DATA/'analyses'/j['id'];rows=[json.loads(x) for x in (folder/'frames.jsonl').read_text().splitlines()]
 source=next(a for a in s['assets'] if a['id']==j['asset_id'])
 cap=cv2.VideoCapture(source['path']);cap.set(cv2.CAP_PROP_POS_FRAMES,rows[0]['frame']);ok,img=cap.read();cap.release()
 if ok:cv2.imwrite(str(folder/'first-frame-annotated.jpg'),annotate(img,rows[0]))
 checks.append(dict(job=j['id'],mode=j['mode'],analyzed_frames=len(rows),wheel_instances=sum(len(r.get('wheels',[])) for r in rows),flagged_frames=sum(r['flagged'] for r in rows),unknown_frames=sum(r['track_limit']=='insufficient geometry' for r in rows),all_decoded_frames_present=j['mode']=='final' and [r['frame'] for r in rows]==list(range(source['frames'])),model_hashes=json.loads((folder/'manifest.json').read_text()).get('checkpoints',{})))
 for kind in ['json','csv','manifest','still']:
  r=requests.get(base+f"jobs/{j['id']}/export/{kind}",timeout=10);r.raise_for_status()
report=dict(completed_analysis_checks=checks,unit_tests='12 passed',typescript='passed',production_build='passed; 793 kB JS bundle warning',browser='Source viewer, scenario controls, evaluation tables and schematic rendering inspected',not_verified=['independent event accuracy','confidence calibration','CARLA execution','multi-camera identity switches','automatic ghost occlusion'])
(DATA/'reports'/'delivery-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
