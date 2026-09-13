import json, sqlite3, threading, time, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
for name in ['datasets','analyses','uploads','models','reports']:
    (DATA/name).mkdir(exist_ok=True)
LOCK = threading.RLock()
def connect():
    c=sqlite3.connect(DATA/'studio.db', timeout=30)
    c.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT, payload TEXT)')
    return c
def put(kind, value):
    value.setdefault('id',uuid.uuid4().hex)
    value['updated_at']=time.time()
    with LOCK, connect() as c:
        c.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)',(value['id'],kind,json.dumps(value)))
    return value
def get(id):
    with connect() as c: row=c.execute('SELECT payload FROM records WHERE id=?',(id,)).fetchone()
    if not row: raise KeyError(id)
    return json.loads(row[0])
def listing(kind):
    with connect() as c: rows=c.execute('SELECT payload FROM records WHERE kind=? ORDER BY rowid DESC',(kind,)).fetchall()
    return [json.loads(r[0]) for r in rows]
