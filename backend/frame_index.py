"""Exact-frame lookup; sampled preview results never stand in for other frames."""
import json,threading
_cache={}
_lock=threading.Lock()
def invalidate(path):
    with _lock:_cache.pop(str(path),None)
def read_frame(path,number):
    if not path.exists():return {}
    with _lock:
        size=path.stat().st_size
        entry=_cache.get(str(path))
        if entry is None or size<entry['offset']:
            entry={'offset':0,'frames':{}};_cache[str(path)]=entry
        with path.open('rb') as stream:
            stream.seek(entry['offset'])
            while True:
                offset=stream.tell();line=stream.readline()
                if not line or not line.endswith(b'\n'):break
                try:r=json.loads(line)
                except json.JSONDecodeError:continue
                entry['frames'][r['frame']]=offset;entry['offset']=stream.tell()
            if number not in entry['frames']:
                return dict(frame=number,cars=[],wheels=[],boundary_candidates=[],track_limit='frame not analyzed',confidence=None,evidence='This exact frame has no saved result. Preview samples are not substituted.')
            stream.seek(entry['frames'][number]);return json.loads(stream.readline())
