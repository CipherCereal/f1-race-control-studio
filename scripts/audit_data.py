"""Validate complete frame accounting and dataset provenance without inventing labels."""
import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA,ROOT,listing
from scripts.acquire import usage
import cv2,numpy as np
def dhash(image):
    g=cv2.resize(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),(9,8));return np.packbits(g[:,1:]>g[:,:-1]).tobytes().hex()
def main():
    sources=json.loads((DATA/'source_catalog.json').read_text());sources['used_bytes']=usage()
    (DATA/'source_catalog.json').write_text(json.dumps(sources,indent=2))
    jobs=[]
    for j in listing('job'):
        if j['status']!='complete':continue
        rows=[json.loads(x) for x in (DATA/'analyses'/j['id']/'frames.jsonl').open()]
        frames=[r['frame'] for r in rows]
        jobs.append(dict(job=j['id'],rows=len(rows),unique_frames=len(set(frames)),contiguous=frames==list(range(len(frames))),flags=sum(r['flagged'] for r in rows),insufficient_geometry=sum(r['track_limit']=='insufficient geometry' for r in rows),detected_car_instances=sum(len(r['cars']) for r in rows),precision_recall='unavailable: no frame-level truth labels',interpretation='zero flags does not imply no violations'))
    p=DATA/'datasets'/'detector-prepared'/'manifest.json';manifest=json.loads(p.read_text());hashes={};cross=[]
    for r in manifest:
        if r['sha256'] in hashes and hashes[r['sha256']]!=r['split']:cross.append(r['path'])
        hashes[r['sha256']]=r['split']
    fingerprints=[]
    for r in manifest:
        image=cv2.imread(r['path']);fingerprints.append(int(dhash(image),16))
    near=[]
    for i,a in enumerate(manifest):
        for k in range(i):
            if a['split']!=manifest[k]['split'] and (fingerprints[i]^fingerprints[k]).bit_count()<=3:near.append([a['path'],manifest[k]['path']])
    heldout_matches=[];source=ROOT.parent/'videoplayback (1).mp4';cap=cv2.VideoCapture(str(source));idx=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        h=int(dhash(frame),16)
        for i,f in enumerate(fingerprints):
            if (h^f).bit_count()<=3:heldout_matches.append({'frame':idx,'training_image':manifest[i]['path']})
        idx+=1
    cap.release()
    report=dict(dataset_bytes=usage(),budget_bytes=50_000_000_000,within_budget=usage()<=50_000_000_000,exact_cross_split_duplicates=cross,near_duplicate_candidates=near,heldout_duplicate_candidates=heldout_matches,heldout_frames_fingerprinted=idx,near_duplicate_method='64-bit difference hash; Hamming <=3, candidate review required; not a proof of absence',training_source_groups=['formula1-box broadcast'],user_video='held out; no labels used for training',analyses=jobs)
    (DATA/'reports'/'data-quality.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':main()
