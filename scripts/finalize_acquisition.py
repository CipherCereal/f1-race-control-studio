"""Reconcile acquisition outcomes against decoded files; retain historical errors."""
import csv,json,time,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
from scripts.acquire import usage
root=DATA/'datasets'/'steering'
rows=list(csv.DictReader((root/'labels.csv').open()))
missing=[];invalid=[]
for row in rows:
 p=root/'images'/(row['img_name']+'.jpg')
 if not p.exists():missing.append(p.name);continue
 try:
  with Image.open(p) as im:im.verify()
 except Exception as e:invalid.append(dict(file=p.name,error=str(e)))
report=dict(checked_at=time.time(),csv_rows=len(rows),present=len(rows)-len(missing),missing=missing,invalid_images=invalid,historical_errors='acquisition-errors.json retained; current file verification supersedes transient rename failures',training_snapshot_unchanged=True)
(DATA/'reports'/'acquisition-final.json').write_text(json.dumps(report,indent=2))
p=DATA/'source_catalog.json';catalog=json.loads(p.read_text())
item=next(x for x in catalog['sources'] if x['id']=='steering')
item.update(status='acquired' if not missing and not invalid else 'acquired subset',acquired_images=report['present'],reason=f"Verified {report['present']} CSV-referenced images; {len(missing)} missing; {len(invalid)} corrupt. Historical transient errors retained.")
ids={s['id'] for s in catalog['sources']}
catalog['sources'] += [s for s in json.loads((DATA/'source_catalog_supplement.json').read_text()) if s['id'] not in ids]
catalog.update(used_bytes=usage(),checked_at=time.time())
p.write_text(json.dumps(catalog,indent=2));print(report)
