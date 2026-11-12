"""Find measured earlier cache values, without inventing a physical copy time."""
from pathlib import Path
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
N = R / 'artifacts/th14/low-pause-input-key-native-nov09/input-key-prefix'
bindings = {}
def raw(p):
    b = p.read_bytes()
    bindings[p.relative_to(R).as_posix()] = hashlib.sha256(b).hexdigest()
    return b
q = json.loads(raw(H / 'qualified.json'))
assert q['allChildrenWorkersHostsGpuAndClockRetired']
assert not q['rawDifferenceCounts']['state32'] and not q['slotDifferenceCounts']
first = q['firstRawDifferences']['camera75']['cppCallback']
assert first == 30828 and q['rawStrict113Prefix'] == first - 1
nb, tail, cb = raw(N / 'world-camera.raw'), raw(N / 'world-camera-tail.u32'), raw(H / 'current-prefix/observations.u32')
assert len(nb) == 35000 * 292 and len(tail) == 35000 * 8 and len(cb) == 35000 * 456
native = lambda i: nb[(i-1)*292:i*292] + tail[(i-1)*8:i*8]
current = lambda i: cb[(i-1)*456+132:(i-1)*456+432]
pose = lambda b: b[:96] + b[224:]
assert pose(native(first)) == pose(current(first))
def ranges(values):
    result=[]
    for v in values:
        if result and v == result[-1][1]+1:result[-1][1]=v
        else:result.append([v,v])
    return result
cases=[]
for owner, target in [('native', native(first)), ('currentCpp', current(first))]:
    cache=target[96:224]
    searches=[]
    for name, getter in [('native',native),('currentCpp',current)]:
        matches=[i for i in range(1,first) if getter(i)[96:224] == cache]
        searches.append(dict(observedOwner=name, earlierMeasuredCacheMatches=len(matches),
                             matchingCallbackRanges=ranges(matches),
                             latestMatch=matches[-1] if matches else None))
    cases.append(dict(owner=owner, cacheSha256=hashlib.sha256(cache).hexdigest(), earlierObservations=searches))
changed={}
for i in range(first,35001):
    n,c=struct.unpack('<75I',native(i)),struct.unpack('<75I',current(i))
    for field in range(75):
        if n[field] != c[field]:changed[field]=changed.get(field,0)+1
assert set(changed) <= set(range(24,56))
raw(Path(__file__))
out=dict(schema='thp/th14-measured-camera-cache-lineage/1', diagnosticOnly=True,
         firstDifferentCallback=first, allNonCacheWordsExact=True, differenceCounts=changed,
         cases=cases, actualEarlierRawCacheObservationsOnly=True,
         physicalCopyTimestampOrWriterProven=False, screenOrPerspectiveModeNotInferred=True,
         noCameraFieldsNormalized=True, noNewGameGpuOrHelperProcess=True,
         productionChanged=False, completeGame=False, bindings=bindings)
path=H/'camera-measured-lineage.json';assert not path.exists()
path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k!='bindings'},indent=2))
