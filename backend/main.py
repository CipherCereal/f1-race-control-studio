import hashlib,json,shutil,threading,zipfile,os
from pathlib import Path
import cv2
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from .store import ROOT,DATA,listing,get,put
from .jobs import start,submit,CANCEL
from .simulation import simulate,carla_status
from .geometry import fit_ground_plane,project_trajectory
app=FastAPI(title='Ghost Rival Studio',version='0.1.0')
from .openf1 import router as openf1_router
app.include_router(openf1_router)
from .precedent.router import router as precedent_router
app.include_router(precedent_router)
@app.get('/api/compute')
def compute():
    from .compute import compute_status
    return compute_status()
def asset(path,held_out=False):
    for a in listing('asset'):
        if a['path']==str(path):return a
    c=cv2.VideoCapture(str(path));fps=c.get(5);frames=int(c.get(7));w=int(c.get(3));h=int(c.get(4));c.release()
    if fps<=0 or frames<=0:raise HTTPException(400,'Cannot decode video')
    a=put('asset',dict(name=path.name,path=str(path),fps=fps,frames=frames,width=w,height=h,duration=frames/fps,held_out=held_out,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),schema_version=1))
    c=cv2.VideoCapture(str(path));c.set(0 if False else cv2.CAP_PROP_POS_MSEC,70000 if frames/fps>70 else 0);ok,frame=c.read();c.release()
    if ok:cv2.imwrite(str(DATA/'uploads'/f"{a['id']}.jpg"),frame)
    return a
@app.on_event('startup')
def init():
    source=ROOT.parent/'videoplayback (1).mp4'
    if source.exists():asset(source,True)
    for j in ([] if os.environ.get('STUDIO_PRESERVE_RUNNING_JOBS')=='1' else listing('job')):
        if j['status'] in ('queued','running'):j['status']='interrupted';put('job',j)
@app.get('/api/state')
def state():
    from .jobs import reconcile_workers
    reconcile_workers()
    cat=DATA/'source_catalog.json';report=DATA/'reports'/'evaluation.json'
    catalog=json.loads(cat.read_text()) if cat.exists() else {'sources':[]}
    supplement=DATA/'source_catalog_supplement.json'
    if supplement.exists():
        ids={s['id'] for s in catalog['sources']}
        catalog['sources'] += [s for s in json.loads(supplement.read_text()) if s['id'] not in ids]
    evaluation=json.loads(report.read_text()) if report.exists() else {'status':'not evaluated'}
    for name in ['steering-evaluation','wheel-evaluation','baseline-comparison','data-quality']:
        p=DATA/'reports'/(name+'.json')
        if p.exists():evaluation[name]=json.loads(p.read_text())
    return dict(assets=listing('asset'),jobs=listing('job'),datasets=catalog,evaluation=evaluation,models=[p.name for p in (DATA/'models').glob('*.pt')],carla=carla_status(),annotations=listing('annotation'),scenarios=listing('scenario'))
@app.post('/api/assets')
async def upload(file:UploadFile=File(...)):
    import uuid
    path=DATA/'uploads'/(uuid.uuid4().hex+Path(file.filename or 'video.mp4').suffix)
    size=0
    with path.open('wb') as out:
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size>5_000_000_000:raise HTTPException(413,'Video exceeds 5 GB upload limit')
            out.write(chunk)
    result=asset(path)
    result['name']=Path(file.filename or 'Imported video').name
    return put('asset',result)
def safe_get(id):
    try:return get(id)
    except KeyError:raise HTTPException(404,'Not found')
@app.get('/api/assets/{id}/video')
def video(id:str):return FileResponse(safe_get(id)['path'],media_type='video/mp4')
@app.get('/api/assets/{id}/poster')
def poster(id:str):safe_get(id);return FileResponse(DATA/'uploads'/f'{id}.jpg')
class JobRequest(BaseModel):
    asset_id:str
    mode:str='preview'
    calibration:dict=Field(default_factory=dict)
@app.post('/api/jobs')
def newjob(body:JobRequest):
    if body.mode not in ('preview','final'):raise HTTPException(400,'Invalid mode')
    a=safe_get(body.asset_id);c=body.calibration
    if c:
        from shapely.geometry import Polygon
        try:
            polygon=c.get('polygon',[]);contacts=c.get('contacts',[])
            if len(polygon)<3 or not Polygon(polygon).is_valid:raise ValueError('Track polygon must contain at least three valid vertices')
            if contacts and (len(contacts)!=4 or any(len(p)<3 or not Polygon(p).is_valid for p in contacts)):raise ValueError('Provide four valid tire contact polygons')
            if any(not 0<=float(v)<=1 for p in [polygon]+contacts for point in p for v in point):raise ValueError('Image coordinates must be normalized from 0 to 1')
            if c.get('confidence') is not None and not 0<=float(c['confidence'])<=1:raise ValueError('Analyst confidence must be between 0 and 1')
            if not 0<=c.get('start_frame',0)<=c.get('end_frame',0)<a['frames']:raise ValueError('Invalid geometry frame interval')
        except Exception as e:raise HTTPException(422,str(e))
    return submit(a,body.mode,c)
@app.post('/api/jobs/{id}/cancel')
def cancel(id:str,bridge:bool=False):
    job=safe_get(id)
    if job['status'] not in ('queued','running'):return {'status':job['status']}
    (DATA/'analyses'/id).mkdir(exist_ok=True)
    (DATA/'analyses'/id/'cancel.request').touch()
    if id in CANCEL:CANCEL[id].set()
    elif not bridge:
        # Compatibility bridge for the original worker, which predates shared cancellation.
        import requests
        try:requests.post(f'http://127.0.0.1:8765/api/jobs/{id}/cancel?bridge=true',json={},timeout=3)
        except requests.RequestException:pass
    return {'status':'cancellation requested'}
@app.post('/api/jobs/{id}/resume')
def resume(id:str):
    j=safe_get(id)
    if j['status'] not in ('cancelled','interrupted','failed','incomplete'):raise HTTPException(409,'Job cannot be resumed')
    return start(safe_get(j['asset_id']),resume=j)
@app.get('/api/jobs/{id}/frame')
def frame_result(id:str,frame:int=0):
    j=safe_get(id);path=DATA/'analyses'/id/'frames.jsonl'
    from .frame_index import read_frame
    return read_frame(path,frame)
@app.get('/api/jobs/{id}/events')
def events(id:str):
    safe_get(id);p=DATA/'analyses'/id/'events.json';return json.loads(p.read_text()) if p.exists() else []
@app.get('/api/jobs/{id}/frames')
def frame_window(id:str,start:int=0,count:int=120):
    safe_get(id)
    if start<0 or not 1<=count<=240:raise HTTPException(422,'Invalid frame window')
    from .frame_index import read_frame
    path=DATA/'analyses'/id/'frames.jsonl'
    return [read_frame(path,i) for i in range(start,start+count)]
@app.get('/api/jobs/{id}/export/{kind}')
def export(id:str,kind:str):
    j=safe_get(id)
    if j['status'] not in ('complete','cancelled','incomplete'):raise HTTPException(409,'Export is not ready')
    names={'video':'annotated.mp4','csv':'events.csv','json':'events.json','manifest':'manifest.json','still':'first-frame.jpg'}
    if kind not in names:raise HTTPException(404)
    p=DATA/'analyses'/id/names[kind]
    if kind=='video' and (p.parent/'annotated-h264.mp4').exists():p=p.parent/'annotated-h264.mp4'
    if kind=='still' and (p.parent/'first-frame-annotated.jpg').exists():p=p.parent/'first-frame-annotated.jpg'
    if not p.exists():raise HTTPException(409,'Export is not ready')
    return FileResponse(p,filename=p.name)
class Scenario(BaseModel):
    duration:float=Field(10,gt=0,le=60)
    gap:float=8
    speed:float=Field(20,ge=0,le=120)
    braking:float=Field(3,ge=0)
    deceleration:float=Field(3,ge=0,le=20)
    mode:str='parametric'
@app.post('/api/scenarios')
def scenario(s:Scenario):
    if s.mode not in ('parametric','responsive'):raise HTTPException(400,'Use telemetry for recorded replay')
    return put('scenario',simulate(**s.model_dump()))
class SessionRequest(BaseModel):
    year:int=Field(2024,ge=2018,le=2030)
    event:str
    session:str='Q'
    driver:str
@app.post('/api/telemetry')
def telemetry(req:SessionRequest):
    try:
        import fastf1
        cache=DATA/'telemetry-cache';cache.mkdir(exist_ok=True);fastf1.Cache.enable_cache(str(cache))
        session=fastf1.get_session(req.year,req.event,req.session);session.load(weather=False,messages=False)
        lap=session.laps.pick_drivers(req.driver).pick_fastest();t=lap.get_telemetry()
        cols=[x for x in ['Speed','Throttle','Brake','X','Y','Z'] if x in t]
        rows=t[cols].copy();rows['time']=t['Time'].dt.total_seconds()
        return put('telemetry',dict(request=req.model_dump(),rows=json.loads(rows.to_json(orient='records')),provenance='external FastF1; merged/interpolated telemetry',alignment_status='unmatched: supply time and geometry anchors',units={'Speed':'km/h','Time':'seconds','position':'source units; verify before projection'}))
    except Exception as e:raise HTTPException(422,str(e))
@app.post('/api/annotations')
def annotations(body:dict):return put('annotation',body)

@app.post('/api/registration')
def registration(body:dict):
    try:
        result=fit_ground_plane(body['world_points'],body['image_points'])
        result.update(asset_id=body.get('asset_id'),start_frame=body.get('start_frame'),end_frame=body.get('end_frame'),provenance='analyst anchors + estimated planar homography')
        return put('registration',result)
    except Exception as e:raise HTTPException(422,str(e))

@app.post('/api/scenarios/project')
def project(body:dict):
    try:return {'projection':project_trajectory(safe_get(body['registration_id'])['matrix'],safe_get(body['scenario_id'])['trajectory']),'status':'schematic ground-plane projection; occlusion unverified'}
    except Exception as e:raise HTTPException(422,str(e))

@app.post('/api/scenarios/replay')
def recorded_replay(body:dict):
    t=safe_get(body['telemetry_id']);rows=t.get('rows',[])
    if not rows or not all('X' in r and 'Y' in r for r in rows):raise HTTPException(422,'Position telemetry unavailable')
    return put('scenario',dict(mode='recorded reference',trajectory=[dict(time=r['time'],x=r['X'],y=r['Y'],speed=r.get('Speed')) for r in rows],units='FastF1 source units: not yet registered to footage',provenance='external recorded telemetry, possibly interpolated',ego_path='fixed recorded video',requires_registration=True))

from fastapi.staticfiles import StaticFiles
fault_mech_dir = ROOT/'dist'/'client'/'fault-mechanism' if (ROOT/'dist'/'client'/'fault-mechanism').exists() else (ROOT/'public'/'fault-mechanism')
if fault_mech_dir.exists():
    app.mount('/fault-mechanism', StaticFiles(directory=fault_mech_dir, html=True), name='fault_mechanism')
precedent_dir = ROOT/'dist'/'client'/'precedent' if (ROOT/'dist'/'client'/'precedent').exists() else (ROOT/'public'/'precedent')
if precedent_dir.exists():
    app.mount('/precedent', StaticFiles(directory=precedent_dir, html=True), name='precedent')
if (ROOT/'public'/'models').exists():
    app.mount('/models', StaticFiles(directory=ROOT/'public'/'models'), name='public_models')
if (ROOT/'dist'/'client').exists():
    app.mount('/',StaticFiles(directory=ROOT/'dist'/'client',html=True),name='dashboard')

