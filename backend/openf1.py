"""Cached historical OpenF1 adapter. No footage is uploaded to OpenF1."""
import hashlib,json,threading,time
from datetime import datetime,timedelta
import requests
from fastapi import APIRouter,HTTPException
from .store import DATA
router=APIRouter(prefix='/api/openf1');lock=threading.Lock();last_request=0

@router.get('/showcases')
def showcases():
 path=DATA/'showcase'/'catalog.json'
 return json.loads(path.read_text()) if path.exists() else []

@router.get('/showcases/{name}')
def showcase(name:str):
 if name not in ('singapore-2024','spain-2024'):raise HTTPException(404,'Showcase not found')
 path=DATA/'showcase'/(name+'.json')
 if not path.exists():raise HTTPException(404,'Showcase data not acquired yet')
 return json.loads(path.read_text())
def fetch(endpoint,params):
 global last_request
 cache=DATA/'openf1-cache';cache.mkdir(exist_ok=True)
 key=hashlib.sha256(json.dumps([endpoint,params],sort_keys=True).encode()).hexdigest();path=cache/(key+'.json')
 if path.exists() and time.time()-path.stat().st_mtime<86400:return json.loads(path.read_text())
 with lock:
  delay=max(0,2.1-(time.monotonic()-last_request))
  if delay:time.sleep(delay)
  last_request=time.monotonic()
  response=requests.get('https://api.openf1.org/v1/'+endpoint,params=params,timeout=30)
  if response.status_code in (401,403):raise HTTPException(503,'OpenF1 access unavailable. Live sessions require separate authorized access; choose a historical session.')
  if response.status_code==429:raise HTTPException(429,'OpenF1 rate limit reached. Retry shortly; cached results remain available.')
  response.raise_for_status();result=response.json();path.write_text(json.dumps(result));return result
@router.get('/sessions')
def sessions(year:int=2023):
 if not 2023<=year<=2030:raise HTTPException(422,'OpenF1 historical sessions start in 2023')
 try:return fetch('sessions',{'year':year})
 except requests.RequestException as e:raise HTTPException(502,str(e))
@router.get('/circuit')
def circuit(session_key:int,driver_number:int=1):
 try:
  session=fetch('sessions',{'session_key':session_key})
  if not session:raise HTTPException(404,'Session not found')
  drivers=fetch('drivers',{'session_key':session_key})
  laps=fetch('laps',{'session_key':session_key,'driver_number':driver_number})
  valid=[r for r in laps if r.get('lap_duration') and r.get('date_start') and not r.get('is_pit_out_lap')]
  if not valid:return dict(session=session[0],drivers=drivers,lap=None,locations=[],telemetry=[],status='No complete lap available for selected driver')
  lap=min(valid,key=lambda r:r['lap_duration']);start=lap['date_start'];end=(datetime.fromisoformat(start)+timedelta(seconds=lap['lap_duration'])).isoformat()
  params={'session_key':session_key,'driver_number':driver_number,'date>':start,'date<':end}
  locations=fetch('location',params);telemetry=fetch('car_data',params)
  return dict(session=session[0],drivers=drivers,lap=lap,locations=locations,telemetry=telemetry,source='https://openf1.org/docs/',status='Recorded reference lap; not synchronized to video',geometry='Approximate driver location trace, not legal track edges',units={'speed':'km/h','position':'OpenF1 source coordinates'})
 except requests.RequestException as e:raise HTTPException(502,str(e))
