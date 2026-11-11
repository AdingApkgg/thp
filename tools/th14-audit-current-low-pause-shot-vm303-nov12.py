"""Compare every captured shot VM field; leave unresolved native links unknown."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import ast
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/current-low-pause-transition-nov12'
NH = R / 'artifacts/th14/low-pause-input-key-native-nov09'
N, A = NH / 'input-key-prefix', H / 'current-prefix'
bindings = {}


def raw(path):
    data = path.read_bytes()
    bindings[path.relative_to(R).as_posix()] = hashlib.sha256(data).hexdigest()
    return data


def load(path):
    return json.loads(raw(path))


def w(data,offset):
    return struct.unpack_from('<I',data,offset)[0]


assert not (H/'shot-vm303-qualified.json').exists()
q = load(H/'qualified.json')
assert q['allChildrenWorkersHostsGpuAndClockRetired']
helper = R/'tools/th14-native-title-live-compare-oct27.py'
source = raw(helper)
assert hashlib.sha256(source).hexdigest() == 'c7866f2c3d6e030bae1e4c5153b196f7500436b43e710fc181730bf087a3f9cc'
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == 'native_words')


class KeepUnknownLink(ast.NodeTransformer):
    def visit_FunctionDef(self,node):
        if node.name != 'handle':
            return self.generic_visit(node)
        # Resolve only actual addresses measured in this same snapshot. A
        # typed marker cannot accidentally compare equal to any u32 word.
        node.body = ast.parse('''
if not address:return 0
if address in by_address:return by_address[address]
return {'unmeasuredNativeVmAddress':address}
''').body
        return node


function = KeepUnknownLink().visit(function)
module = ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
env = dict(struct=struct)
exec(compile(module,str(helper),'exec'),env)
convert = env['native_words']
nindex,cindex = load(N/'shot-index.json'),load(A/'shot-index.json')
cp = {tuple(r['inputKey']):r for r in cindex['snapshots']}
ndata = raw(N/'shot-snapshots.bin')
expanded_raw = raw(A/'expanded-shot-vms.u32')
expanded_meta = load(A/'expanded-vm-report.json')
assert hashlib.sha256(expanded_raw).hexdigest() == expanded_meta['shotVmSha256']
expanded = {}
for record in struct.iter_unpack('<307I',expanded_raw):
    key = (record[0],record[3])
    assert key not in expanded
    expanded[key] = record[4:]
assert len(expanded) == expanded_meta['shotVmRows']
counts,unmeasured_counts = Counter(),Counter()
differences,unmeasured = [],[]
compared = Counter()
records = 0
for item in nindex['snapshots']:
    if tuple(item['inputKey']) not in cp:continue
    blob = ndata[item['offset']:item['offset']+item['bytes']]
    assert hashlib.sha256(blob).hexdigest() == item['sha256']
    ncb,ccb = item['callback'],cp[tuple(item['inputKey'])]['callback']
    captured = []
    by_address = {}
    for slot in range(256):
        at = 256+slot*1788
        meta = struct.unpack_from('<8I',blob,at)
        if not meta[1] or not meta[5]&4:
            continue
        vm = blob[at+32+0xd0+64:at+1788]
        assert len(vm) == 0x5cc and w(vm,0x540) == meta[2]
        assert w(vm,0x570) == meta[4]
        assert meta[4] not in by_address or by_address[meta[4]] == meta[2]
        by_address[meta[4]] = meta[2]
        captured.append((slot,vm))
    for slot,vm in captured:
        row = dict(rawVmHex=vm.hex(),handle=w(vm,0x540),
            file=struct.unpack_from('<H',vm,0x36)[0],
            script=struct.unpack_from('<H',vm,0x4aa)[0],
            timerPrevious=w(vm,0x548),timerCurrent=w(vm,0x54c),timerFraction=w(vm,0x550),
            pendingInterrupt=w(vm,0x4a0),ageCurrent=w(vm,0x560))
        fields,values = convert(row,by_address)
        p = expanded[ccb,slot]
        assert len(values) == len(fields) == len(p) == 303
        assert len(values[0:3]) == len(p[0:3]) == 3
        records += 1
        for field,n,c in zip(fields,values,p,strict=True):
            if isinstance(n,dict):
                assert field in ['parentHandle','registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle']
                unmeasured_counts[field] += 1
                unmeasured.append(dict(nativeCallback=ncb,cppCallback=ccb,inputKey=item['inputKey'],
                    slot=slot,handle=values[0],field=field,**n,cppValueNotUsedAsNativeReference=c))
                continue
            compared[field] += 1
            if n != c:
                counts[field] += 1
                differences.append(dict(nativeCallback=ncb,cppCallback=ccb,inputKey=item['inputKey'],
                    slot=slot,handle=values[0],file=values[1],script=values[2],field=field,native=n,cpp=c))
assert records == len(expanded)
assert sum(compared.values())+sum(unmeasured_counts.values()) == records*303
raw(Path(__file__))
out = dict(updatedUtc=datetime.now(timezone.utc).isoformat(),diagnosticOnly=True,
    snapshotPairs=len(cp),capturedVmPairs=records,canonicalFieldCount=303,
    comparedWords=sum(compared.values()),differentFields=dict(counts),differentWords=len(differences),
    unmeasuredNativeLinkWords=sum(unmeasured_counts.values()),unmeasuredLinksByField=dict(unmeasured_counts),
    actualSameSnapshotNativeAddressesUsedForLinks=True,zeroOrCppOutputNotSubstitutedForUnknownLinks=True,
    allComparedMeasuredWordsExact=not differences,
    complete303WordsPerVmAccepted=not differences and not unmeasured,
    completeGlobalRegistryOrEveryVmHistoryCaptured=False,
    originalCallbacksAndLiteralHandlesPreserved=True,newGameOrGpuStarted=False,
    productionChanged=False,oldStrictFailuresUnchanged=True,completeGame=False,
    currentGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',
    ordinaryInitialLoadOrAllModesAccepted=False,bindings=bindings)
(H/'shot-vm303-qualified.json').write_text(json.dumps(out,indent=2)+'\n')
(H/'shot-vm303-private-differences.json').write_text(json.dumps(differences,indent=2)+'\n')
(H/'shot-vm303-private-unmeasured-links.json').write_text(json.dumps(unmeasured,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['capturedVmPairs','comparedWords','differentWords',
    'differentFields','unmeasuredNativeLinkWords','unmeasuredLinksByField','complete303WordsPerVmAccepted']}))
