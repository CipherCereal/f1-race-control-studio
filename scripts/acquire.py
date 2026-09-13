"""Resumable public-source acquisition. No credentials or protected media bypass."""
import concurrent.futures, hashlib, json, sys, time, zipfile, threading
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
BASE=DATA/'datasets'; LIMIT=50_000_000_000
_budget_lock=threading.Lock()
_download_bytes=None
CATALOG=[
 dict(id='formula1-box',url='https://www.kaggle.com/datasets/gazeux330000/formula1-box',license='Apache 2.0 (publisher declaration)',labels=['car boxes','team'],kind='F1 images',status='pending'),
 dict(id='steering',url='https://huggingface.co/datasets/daniel-saed/F1-steering-angle-dataset',license='MIT (publisher declaration; underlying footage separately unverified)',labels=['steering wheel angle'],kind='onboard images',status='pending'),
 dict(id='formula-one-cars',url='https://www.kaggle.com/datasets/vesuvius13/formula-one-cars',license='unverified',labels=['classification'],kind='F1 images',status='pending'),
 dict(id='track-limits',url='https://universe.roboflow.com/nikshithas-workspace/f1-race-track-limits',license='CC BY 4.0 (listing)',labels=['track_inside','track_outside'],kind='images',status='blocked',reason='Listing has 124 images but no published dataset version; precise masks unverified'),
 dict(id='vroom',url='https://varun-bharadwaj.github.io/vroom/',license='unverified',labels=['reconstruction research'],kind='F1 onboard research',status='reference',reason='Linked repository returned 404; no verified downloadable footage'),
 dict(id='racecar',url='https://registry.opendata.aws/racecar-dataset/',license='CC BY-NC 4.0',labels=['multisensor tracks'],kind='Indy research',status='reference',reason='Large non-F1 sensor corpus; prioritize F1 assets within budget'),
 dict(id='a2rl',url='https://tum-avs.github.io/A2RL_Dataset_website/',license='requires inspection',labels=['LiDAR','RADAR'],kind='autonomous racing',status='reference',reason='Sensor-focused supplementary source; not F1 wheel labels')]
def usage():
    total=0
    for p in BASE.rglob('*'):
        try:
            if p.is_file():total+=p.stat().st_size
        except FileNotFoundError:pass
    return total
def save():
    (DATA/'source_catalog.json').write_text(json.dumps({'schema_version':1,'budget_bytes':LIMIT,'used_bytes':usage(),'sources':CATALOG,'checked_at':time.time()},indent=2))
def download(url,path):
    global _download_bytes
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): return
    r=requests.get(url,stream=True,timeout=(20,120));r.raise_for_status()
    size=int(r.headers.get('Content-Length',0))
    tmp=path.with_suffix(path.suffix+'.part')
    with _budget_lock:
        if _download_bytes is None:_download_bytes=usage()
        if _download_bytes+size>LIMIT:raise RuntimeError('Dataset budget exceeded')
        if tmp.exists():_download_bytes-=tmp.stat().st_size
    with tmp.open('wb') as f:
        for chunk in r.iter_content(1024*1024):
            with _budget_lock:
                if _download_bytes+len(chunk)>LIMIT:raise RuntimeError('Dataset budget exceeded')
                _download_bytes+=len(chunk)
            f.write(chunk)
    tmp.replace(path)
def kaggle(item,ref):
    global _download_bytes
    path=BASE/item['id']/'source.zip'
    download('https://www.kaggle.com/api/v1/datasets/download/'+ref,path)
    with zipfile.ZipFile(path) as z:
        if usage()+sum(x.file_size for x in z.infolist())>LIMIT: raise RuntimeError('Extracted data exceeds budget')
        target=path.parent/'extracted'; target.mkdir(exist_ok=True)
        for info in z.infolist():
            dst=(target/info.filename).resolve()
            if not dst.is_relative_to(target.resolve()): raise RuntimeError('Unsafe archive path')
            if not dst.exists():z.extract(info,target)
    item.update(status='acquired',archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path.parent))
    with _budget_lock:_download_bytes=None
def steering(item):
    root='https://huggingface.co/datasets/daniel-saed/F1-steering-angle-dataset/resolve/main/'
    folder=BASE/'steering';download(root+'dataset_backup.csv',folder/'labels.csv')
    import csv
    rows=list(csv.DictReader((folder/'labels.csv').open()))
    item['columns']=list(rows[0]);item['rows_available']=len(rows)
    print('Steering CSV',rows[:2],flush=True)
    # Preserve deterministic diversity while obtaining a first trainable slice.
    selected=rows
    (folder/'selection.json').write_text(json.dumps(selected,indent=2))
    names=[]
    for row in selected:
        name=row.get('img_name','')+'.jpg'
        if name:names.append(name)
    def one(name):
        rel=name.replace('\\','/');rel=rel if rel.startswith('all_frames/') else 'all_frames/'+rel.split('/')[-1]
        download(root+rel,folder/'images'/Path(rel).name)
    # Bounded subset fits comfortably within the reserved budget.
    failures=[]
    def checked(name):
        try:one(name)
        except Exception as e:failures.append({'name':name,'error':str(e)})
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(checked,names))
    (folder/'acquisition-errors.json').write_text(json.dumps(failures,indent=2))
    count=len(list((folder/'images').glob('*.jpg')))
    item.update(status='acquired' if not failures else 'acquired subset',acquired_images=count,path=str(folder),reason=f'{count} images; {len(failures)} unavailable or failed; full CSV retained')
if __name__=='__main__':
    existing=DATA/'source_catalog.json'
    if existing.exists():CATALOG[:]=json.loads(existing.read_text())['sources']
    save()
    for item in CATALOG:
        if item['status']!='pending':continue
        try:
            print('Acquiring',item['id'],flush=True)
            if item['id']=='steering':steering(item)
            else:kaggle(item,{'formula1-box':'gazeux330000/formula1-box','formula-one-cars':'vesuvius13/formula-one-cars'}[item['id']])
        except Exception as e:item.update(status='blocked',reason=str(e))
        save();print(item,flush=True)
