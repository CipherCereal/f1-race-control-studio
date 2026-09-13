"""Acquire source-backed OpenF1 showcase bundles; videos remain separate assets."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.openf1 import sessions,circuit,fetch
from backend.store import DATA
folder=DATA/'showcase';folder.mkdir(exist_ok=True)
catalog=[]
for country,video in [('Singapore','https://www.youtube.com/watch?v=3fbDRMmLtbA'),('Spain','https://www.youtube.com/watch?v=pY0XNHVU-b0')]:
 session=next(s for s in sessions(2024) if s['country_name']==country and s['session_name']=='Qualifying')
 data=circuit(session['session_key'],4)
 data['weather']=fetch('weather',{'session_key':session['session_key']})
 data['race_control']=fetch('race_control',{'session_key':session['session_key']})
 data['video_url']=video
 data['synchronization']='Matching session/driver; video timing alignment not yet reviewed'
 slug=country.lower()+'-2024';(folder/(slug+'.json')).write_text(json.dumps(data))
 catalog.append(dict(id=slug,title=f'{country} 2024 - Norris qualifying',video_url=video,session_key=session['session_key'],driver_number=4,locations=len(data['locations']),telemetry=len(data['telemetry'])))
 (folder/'catalog.json').write_text(json.dumps(catalog,indent=2))
 print(catalog[-1],flush=True)
