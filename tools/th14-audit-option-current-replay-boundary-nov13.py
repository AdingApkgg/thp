"""Audit the new owned pair; keep raw callbacks, keys, IDs and missing fields."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import ast
import hashlib
import importlib
import json
import struct
import sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
NH = R / 'artifacts/th14/low-pause-input-key-native-nov09'
N, A = NH / 'input-key-prefix', H / 'current-prefix'
bindings = {}


def raw(path):
    data = path.read_bytes()
    bindings[path.relative_to(R).as_posix()] = hashlib.sha256(data).hexdigest()
    return data


def load(path):
    return json.loads(raw(path))


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


OUT = H / 'qualified.json'
assert not OUT.exists()
nr, cr = load(N/'report.json'), load(A/'report.json')
nreceipt, creceipt = load(NH/'native-terminal-receipt.json'), load(H/'cpp-terminal-receipt.json')
assert nreceipt['reaped'] and creceipt['reaped'] and nreceipt['exitCode'] == 0 and creceipt['exitCode'] == 1
capture_boundary=load(H/'capture-boundary-qualified.json')
assert capture_boundary['passed'] and capture_boundary['captureCompleteAgainstActualFixture']
assert capture_boundary['equivalenceNotInferred'] is True
assert nreceipt['pid'] == nr['pid'] and creceipt['pid'] == cr['pid']
assert nr['childExited'] and not nr['error'] and nr['callbacks'] == 35000
assert not nr['debuggerAttached'] and nr['instructionBytesPatched'] == 6 and nr['rngOrCounterWrites'] == 0
assert nr['caseInitialization']['attractBitClearOnly'] and nr['configuredMusicAndSoundVolumeZero']
assert cr['terminal'] and cr['closed'] and not cr['exception'] and not cr['errors']
assert cr['callbacks'] == 35000 and not cr['captureComplete'] and cr['actualNativeGles']
compared_callbacks = cr['callbacks']
assert all(t['returned'] and not t['error'] for t in cr['workers'])
assert all(t['closed'] and t['exitCode'] == 0 for t in cr['physicalWorkers'])
assert not cr['processClockResolution']['active']
assert cr['processClockResolution']['beginCalls'] == cr['processClockResolution']['endCalls'] == 1
platform = load(A/'platform.json')
assert platform['gpuContextClosed'] and not platform['audibleOutput']
assert not any(platform[k] for k in ['stream','window','context','pendingTimers','openFiles'])
assert not any(platform['liveObjects'].values()) and not any(platform['actualNativeGles']['liveObjects'].values())
assert all(x['result'] == 1 for x in platform['gpuContextCleanup'])
delivery = platform['productionDelivery']
assert not delivery['activeRestore'] and not delivery['activeScene']
assert all(w['exited'] and not w['error'] for w in delivery['workers'])

build_path = H/'component/build.json'
build = load(build_path)
assert cr['wasmSha256'] == build['wasmSha256'] == 'dd321b5be096bce48fbb929457809823a5c10e9c417c43077039ddc5684a1dfa'
for path,digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
    assert hashlib.sha256(raw(R/path)).hexdigest() == digest, path
assert load(H/'host-preflight.json')['setupBindingsVerified']
assert load(H/'driver-prepared.json')['driverSha256'] == cr['driverSha256']
assert hashlib.sha256(raw(R/'tools/th14-run-option-current-replay-nov13.mjs')).hexdigest() == cr['driverSha256']
assert hashlib.sha256(raw(R/'tools/th14-low-pause-input-native-nov09.py')).hexdigest() == nr['sourceSha256']
component = load(NH/'component-0x50000000/verified.json')
assert component['componentVerified'] and component['cases'] == 3644
assert nr['componentSha256'] == hashlib.sha256(raw(NH/'component-0x50000000/verified.json')).hexdigest()
assert nr['generatorSha256'] == component['generatorSha256'] == hashlib.sha256(raw(R/'tools/th14_input_key_shot_logger_x86_nov09.py')).hexdigest()
assert load(A/'plan.json')['replaySha256'] == nr['sourceFullReplaySha256']

native_raw = {}
for name,width,key in [('selected-state.u32',32,'selectedSha256'),('world-camera.raw',73,'worldCameraSha256'),
    ('world-camera-tail.u32',2,'worldCameraTailSha256'),('hud-score.u32',2,'hudScoreSha256'),('replay-cursor.u32',14,'replayCursorSha256')]:
    data = raw(N/name)
    assert len(data) == 35000*width*4 and hashlib.sha256(data).hexdigest() == nr[key]
    native_raw[name] = data
ns = list(struct.iter_unpack('<32I',native_raw['selected-state.u32']))
nc = list(struct.iter_unpack('<14I',native_raw['replay-cursor.u32']))
cpp_raw = raw(A/'observations.u32')
cpp = list(struct.iter_unpack('<114I',cpp_raw))
assert len(cpp) == compared_callbacks and [r[0] for r in cpp] == list(range(1,compared_callbacks+1))
native = []
for i in range(compared_callbacks):
    camera = struct.unpack_from('<73I',native_raw['world-camera.raw'],i*292)+struct.unpack_from('<2I',native_raw['world-camera-tail.u32'],i*8)
    hud = struct.unpack_from('<2I',native_raw['hud-score.u32'],i*8)
    native.append((i+1,ns[i],camera,hud,tuple(nc[i][k] for k in (7,8,3,9))))
portable = [(r[0],r[1:33],r[33:108],r[108:110],r[110:114]) for r in cpp]
kinds = ['state32','camera75','hud2','cursor4']


def difference(a,b):
    return {kind:[i for i,(x,y) in enumerate(zip(left,right,strict=True)) if x != y]
            for kind,left,right in zip(kinds,a[1:],b[1:],strict=True)}


raw_counts = {k:Counter() for k in kinds}
first_raw = {}
prefix = 0
for i,(n,c) in enumerate(zip(native,portable,strict=True)):
    diff = difference(n,c)
    for kind,fields in diff.items():
        raw_counts[kind].update(fields)
        if fields:
            first_raw.setdefault(kind,dict(nativeCallback=n[0],cppCallback=c[0],fields=fields))
    if not any(diff.values()) and prefix == i:
        prefix += 1


def keyed(rows):
    buckets = defaultdict(list)
    outside = []
    for row in rows:
        stage = row[1][30]
        cursor,counter,selected,declared = row[4]
        if stage != selected or not 0 < cursor <= declared:
            outside.append(row[0])
        else:
            buckets[(stage,selected,cursor,counter)].append(row)
    ambiguous = {key:[r[0] for r in rows] for key,rows in buckets.items() if len(rows) != 1}
    return {key:rows[0] for key,rows in buckets.items() if len(rows) == 1},outside,ambiguous


nm,no,na = keyed(native)
cm,co,ca = keyed(portable)
common = sorted(nm.keys() & cm.keys())
coordinate_counts = {k:Counter() for k in kinds}
coordinate_first = {}
matched_stages = Counter()
for key in common:
    matched_stages[key[0]] += 1
    n,c = nm[key],cm[key]
    for kind,fields in difference(n,c).items():
        coordinate_counts[kind].update(fields)
        if fields:
            coordinate_first.setdefault(kind,dict(key=key,nativeCallback=n[0],cppCallback=c[0],fields=fields))

# Read the frozen independent field definitions; do not execute its old run.
field_oracle = R/'tools/th14-audit-native-shot-slots-nov05.py'
oracle_bytes = raw(field_oracle)
assert hashlib.sha256(oracle_bytes).hexdigest() == '835473ad56cd297b1ccdeedab981d349735aa86b0e00a96ed1474c5d742b9c5a'
tree = ast.parse(oracle_bytes)
maps = {}
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['shot_fields','vm_fields'] for t in node.targets):
        # The vm map contains a literal comprehended range; evaluate only the
        # pinned dictionary expression with an empty builtins namespace.
        maps[node.targets[0].id] = eval(compile(ast.Expression(node.value),'pinned-fields','eval'), {'__builtins__':{},'range':range})
assert len(maps) == 2
sys.path[:0] = [str(R/'tools/tmp/th14-analysis-python'),str(R/'tools')]
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_MXCSR,UC_X86_REG_FPCW,UC_X86_REG_FPSW,UC_X86_REG_FPTAG
image = importlib.import_module('th-anm-handlers').handlers(14)[0]
assert hashlib.sha256(image.data).hexdigest() == nr['executableSha256']
m = Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,offset,count in image.sections:
    first = va & ~4095
    m.mem_map(first,((va+size+4095)&~4095)-first)
    m.mem_write(va,image.data[offset:offset+count])
BASE,VM,OUTPUT,STACK,STOP = 0x70000000,0x70001000,0x70003000,0x700ff000,0x700fe000
m.mem_map(BASE,0x100000)
m.mem_write(0x4854a0,b'\xc3')


def quad(vm,globals):
    m.mem_write(VM,vm)
    m.mem_write(OUTPUT,bytes(48))
    m.mem_write(0x4f7a6c,globals)
    m.mem_write(STACK,struct.pack('<II',STOP,OUTPUT))
    for register,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,VM),(UC_X86_REG_MXCSR,0x1f80),
            (UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:
        m.reg_write(register,value)
    m.emu_start(0x479560,STOP,count=100000)
    assert m.reg_read(UC_X86_REG_EIP) == STOP
    return struct.unpack('<12I',m.mem_read(OUTPUT,48))


ni,ci = load(N/'shot-index.json'),load(A/'shot-index.json')
assert len(ni['snapshots']) == 123 and len(ci['snapshots']) > 0
native_snapshots = raw(N/'shot-snapshots.bin')
assert hashlib.sha256(native_snapshots).hexdigest() == nr['shotSnapshotsSha256']
assert len(native_snapshots) == nr['shotSnapshotBytes']
assert ni['slotBytes'] == 1788 and ni['snapshotBytes'] == 457984
np = {tuple(r['inputKey']):r for r in ni['snapshots']}
cp = {tuple(r['inputKey']):r for r in ci['snapshots']}
targets = {tuple(k) for k in build['targetInputKeys']}
assert len(np) == 123 and cp.keys() == targets and targets <= np.keys()
slot_counts,compared,unmeasured = Counter(),Counter(),Counter()
slot_differences = []
slot_summary = []


def check(kind,index,n,c,ncb,ccb,slot):
    compared[kind] += 1
    if n != c:
        slot_counts[kind] += 1
        slot_differences.append(dict(nativeCallback=ncb,cppCallback=ccb,slot=slot,kind=kind,field=index,native=n,cpp=c))


flt = lambda w: struct.unpack('<f',struct.pack('<I',w))[0]
for key in sorted(targets):
    n,c = np[key],cp[key]
    blob = native_snapshots[n['offset']:n['offset']+n['bytes']]
    assert hashlib.sha256(blob).hexdigest() == n['sha256']
    header = struct.unpack_from('<64I',blob)
    assert tuple(header[57:61]) == key
    assert header[1] == n['callback'] and header[9] == header[10] == 0
    assert tuple(header[12:44]) == ns[n['callback']-1]
    assert key == (ns[n['callback']-1][30],nc[n['callback']-1][3],nc[n['callback']-1][7],nc[n['callback']-1][8])
    cdata = raw(A/c['file'])
    assert hashlib.sha256(cdata).hexdigest() == c['sha256']
    prows = list(struct.iter_unpack('<96I',cdata))
    obs = cpp[c['callback']-1]
    assert key == tuple(obs[i] for i in (31,112,110,111))
    check('activeSlotCount',26,header[6],sum(bool(p[1]) for p in prows),n['callback'],c['callback'],-1)
    for slot,p in enumerate(prows):
        at = 256+slot*1788
        meta = struct.unpack_from('<8I',blob,at)
        assert meta[0] == slot
        check('slotState',1,meta[1],p[1],n['callback'],c['callback'],slot)
        if not meta[1] or not p[1]:
            # Inactive raw memory was not captured; never fill it with zeros.
            continue
        shot = blob[at+32:at+32+0xd0]
        assert word(shot,0x98) == meta[1]
        for index,offset in maps['shot_fields'].items():
            check('shotWords',index,word(shot,offset),p[index],n['callback'],c['callback'],slot)
        if meta[5]&2:
            spec = blob[at+32+0xd0:at+32+0xd0+64]
            for index,offset,fmt in [(19,0x21,'b'),(20,0x20,'b'),(24,0x22,'h')]:
                check('specFields',index,struct.unpack_from('<'+fmt,spec,offset)[0]&0xffffffff,p[index],n['callback'],c['callback'],slot)
        else:
            unmeasured['nativeActiveSpecNotCaptured'] += 1
        present = bool(meta[5]&4)
        check('vmPresent',25,int(present),p[25],n['callback'],c['callback'],slot)
        if not present or not p[25]:
            continue
        vm = blob[at+32+0xd0+64:at+1788]
        assert len(vm) == 0x5cc and word(vm,0x540) == meta[2]
        for index,offset in maps['vm_fields'].items():
            check('vmWords',index,word(vm,offset),p[index],n['callback'],c['callback'],slot)
        for index,offset in [(27,0x36),(28,0x4aa)]:
            check('vmIdentity',index,struct.unpack_from('<H',vm,offset)[0],p[index],n['callback'],c['callback'],slot)
        mode = (word(vm,0x18)>>25)&31
        check('vmIdentity',38,mode,p[38],n['callback'],c['callback'],slot)
        if word(vm,0x594) or mode > 3 or not p[66]:
            unmeasured['parentOrModeOrCppQuadNotAvailable'] += 1
            continue
        corners = quad(vm,blob[44*4:53*4])
        for i,value in enumerate(corners):
            check('quadWords',68+i,value,p[68+i],n['callback'],c['callback'],slot)
        left,top = struct.unpack_from('<2i',blob,45*4)
        visible = word(shot,0x1c)<10 or any(left<flt(corners[i*3])<left+384 and top<flt(corners[i*3+1])<top+448 for i in range(4))
        check('quadVisibility',67,int(visible),p[67],n['callback'],c['callback'],slot)
    slot_summary.append(dict(inputKey=key,nativeCallback=n['callback'],cppCallback=c['callback'],nativeActive=header[6],cppActive=sum(bool(p[1]) for p in prows)))

for path in [Path(__file__),NH/'native-prepared.json',H/'driver-prepared.json',H/'native-reference-metadata.json',H/'host-preflight.json']:
    raw(path)
result = dict(updatedUtc=datetime.now(timezone.utc).isoformat(),qualifiedOwnedDiagnosticPair=True,
    nativeCallbacks=35000,cppCallbacks=compared_callbacks,rawComparedCallbacks=compared_callbacks,nativeHasNoDebuggerOrPostResumeSuspensions=True,
    nativeInstrumentationIsSixByteDetourNotUnmodifiedProgram=True,
    actualCallbackNumbersPreserved=True,referenceRowsNotSuppliedToCpp=True,
    rawStrict113Prefix=prefix,rawStrict113AllWordsExact=not any(raw_counts.values()),
    rawDifferenceCounts={k:dict(v) for k,v in raw_counts.items()},firstRawDifferences=first_raw,
    inputCoordinateMatched=len(common),matchedByStage=dict(matched_stages),
    inputCoordinateDifferenceCounts={k:dict(v) for k,v in coordinate_counts.items()},
    firstInputCoordinateDifferences=coordinate_first,
    nativeOutsideIncomingCoordinateCallbacks=no,cppOutsideIncomingCoordinateCallbacks=co,
    nativeAmbiguousKeys=[dict(key=k,callbacks=v) for k,v in na.items()],
    cppAmbiguousKeys=[dict(key=k,callbacks=v) for k,v in ca.items()],
    nativeKeysWithoutCpp=[k for k in nm if k not in cm],cppKeysWithoutNative=[k for k in cm if k not in nm],
    nativeSlotSnapshotPairs=len(targets),firstFormerCountLocationCovered=True,allSevenFormerCountLocationsAccepted=False,
    slotCompared=dict(compared),slotDifferenceCounts=dict(slot_counts),
    unmeasuredSlotCases=dict(unmeasured),slotSnapshots=slot_summary,
    inactiveRawShotWordsNotCapturedOrAccepted=True,completeVm303AndRegistryNotCompared=True,
    cppFullRegistryCheckpointsUnpairedWithNewNative=cr['fullVmSnapshots'],
    geometryIsOriginalFunctionComponentReconstruction=True,originalQuadEntry=0x479560,
    declaredNoopService=0x4854a0,x87ControlWord=0x37f,mxcsr=0x1f80,
    naturalOsExitOrWholeReplayNotAccepted=True,actualPixelsOrFinalPcmNotAccepted=True,
    allChildrenWorkersHostsGpuAndClockRetired=True,productionChanged=False,
    noRngPaddingOrTimeOrIdentityMapping=True,originalScheduleOrAllModesAccepted=False,
    currentGameSource=None,currentGameSourceBase='b8e36ef27d96238352f5edaf9b368ca23394ceb3',localSourceChanges=build['localSourceChanges'],
    ordinaryInitialLoadOrManualEntryAccepted=False,
    oldDebuggerReferenceAndFirstPresentFailuresUnchanged=True,
    completeGame=False,bindings=bindings)
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(H/'slot-private-differences.json').write_text(json.dumps(slot_differences,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(rawStrict113Prefix=prefix,rawStrict113Exact=result['rawStrict113AllWordsExact'],
    inputCoordinateMatched=len(common),inputCoordinateDifferentStateFields=dict(coordinate_counts['state32']),
    slotPairs=len(targets),slotDifferences=dict(slot_counts),unmeasured=dict(unmeasured),
    allOwnedResourcesRetired=True,completeGame=False)))
