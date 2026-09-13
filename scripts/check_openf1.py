import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.openf1 import sessions,circuit
from backend.store import DATA
rows=sessions(2023)
matches=[r for r in rows if r.get('country_name')=='Brazil' and r.get('session_name')=='Qualifying']
if not matches:raise RuntimeError('Brazil qualifying session not returned')
r=circuit(matches[0]['session_key'],1)
report={k:v for k,v in r.items() if k not in ('locations','telemetry','drivers')}
report.update(location_samples=len(r['locations']),telemetry_samples=len(r['telemetry']),drivers=len(r['drivers']))
(DATA/'reports/openf1-verification.json').write_text(json.dumps(report,indent=2));print(report)
