import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/source_catalog_supplement.json'
rows=json.loads(p.read_text())
item=dict(id='wheels-tires-body',url='https://universe.roboflow.com/wheeltirebody/wheels-tires-body/dataset/8',version=8,license='CC BY 4.0 (publisher declaration)',kind='wheel segmentation candidate',labels=['wheel','tire','body','numeric classes'],status='reference',reason='375 source images; 1007 version-8 augmented images. F1 provenance unverified. Download page did not expose an archive in available web extraction; not acquired.')
if not any(r['id']==item['id'] for r in rows):rows.append(item)
p.write_text(json.dumps(rows,indent=2))
