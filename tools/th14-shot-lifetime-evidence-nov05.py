"""Recompute bounded shot retirement evidence; publish no raw VM/RNG state."""
from pathlib import Path
from collections import Counter
import hashlib, importlib, json, struct, sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/shot-lifetime-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
bindings = {}


def raw(path):
    path = path.resolve()
    assert path.is_relative_to(R)
    data = path.read_bytes()
    bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
    return data


def read(path):
    return json.loads(raw(path))


def flt(word):
    return struct.unpack('<f', struct.pack('<I', word))[0]


def key(frame, row):
    # This is a family/birth grouping, not a globally unique shot identity.
    return (frame-row[5], *row[19:25])


def groups(frame, rows):
    return Counter(key(frame, row) for row in rows if row[1])


build = read(H/'build-retry1/observer-build.json')
assert build['engineSourcesRecompiledForThisLink'] == 0
assert build['engineObjectsReusedForThisLink'] == 141
assert not build['rootProductionSourcesModified']
assert SHA(raw(H/'build-retry1/observer.wasm')) == build['wasmSha256']
fixture = R/'runtimes/th12/th12_web/tests/cpp/th14-shot-lifetime-observer-nov05.cpp'
assert SHA(raw(fixture)) == build['observerSourceSha256']
trajectories = {}; snapshots = {}; runs = []
for case in ['off', 'baseline', 'late']:
    home = H/case
    result = read(home/'result.json')
    assert result['exitCode'] == 0 and result['callbacks'] == 35000
    assert result['allSelectedStateBytesEqualPriorRun']
    assert SHA(raw(home/'driver.mjs')) == result['diagnosticDriverSha256']
    data = raw(home/'model/diagnostic-state.u32')
    assert len(data) == 35000*128 and SHA(data) == result['selectedSha256']
    prior_case = 'stage3-player-late' if case == 'late' else 'baseline'
    assert data == raw(R/'artifacts/th14/original-pair-audit-nov05/initialize-controls'/prior_case/'model/diagnostic-state.u32')
    trajectories[case] = list(struct.iter_unpack('<32I', data))
    index = read(home/'model/shot-lifetime-index.json')
    assert len(index['snapshots']) == (0 if case == 'off' else 55)
    found = {}
    for item in index['snapshots']:
        blob = raw(home/'model'/item['file'])
        assert len(blob) == item['bytes'] == 256*96*4
        assert SHA(blob) == item['sha256']
        rows = list(struct.iter_unpack('<96I', blob))
        assert [r[0] for r in rows] == list(range(256))
        selected = trajectories[case][item['callback']-1]
        assert (selected[30], selected[0]) == (item['stage'], item['stageFrame'])
        assert sum(bool(r[1]) for r in rows) == selected[26]
        identity = (item['stage'], item['stageFrame'])
        assert identity not in found
        found[identity] = rows
    snapshots[case] = found
    runs.append(dict(case=case, callbacks=35000, snapshots=len(found),
                     selectedSha256=SHA(data), unchangedFromPriorTrajectory=True))
assert trajectories['off'] == trajectories['baseline']
assert snapshots['baseline'].keys() == snapshots['late'].keys()
count_differences = []
for (stage, frame), before in snapshots['baseline'].items():
    after = snapshots['late'][stage, frame]
    a, b = groups(frame, before), groups(frame, after)
    if a != b:
        changed = sorted(k for k in a.keys() | b.keys() if a[k] != b[k])
        assert len(changed) == 1
        k = changed[0]
        assert max(a[k], b[k]) == 1 and min(a[k], b[k]) == 0
        count_differences.append(dict(stage=stage, stageFrame=frame,
            baseline=sum(a.values()), late=sum(b.values()),
            uniqueDifferingFamilyBirthGroup=True, family=list(k[1:]), birthFrame=k[0]))
assert [(x['stage'], x['stageFrame']) for x in count_differences] == [(3,1479),(3,2093)]


def verify_retirement(slot, previous_frame, retained_case, retired_case):
    frame = previous_frame + 1
    a = snapshots[retained_case][3, previous_frame][slot]
    b = snapshots[retired_case][3, previous_frame][slot]
    assert a[1] == b[1] == 2 and a[25] == b[25] == 1
    assert key(previous_frame,a) == key(previous_frame,b)
    assert a[12:19] == b[12:19] and a[40:49] == b[40:49]
    assert a[50:58] == b[50:58]  # dimensions/scales/pivot unchanged
    assert a[27:29] == b[27:29] == (9,6)
    assert a[37:39] == b[37:39] == (29,1)
    assert a[49] != b[49] and a[84] != b[84]
    for r in [a,b]:
        assert r[30]&0x40 and r[30]&0x800000
        assert abs(flt(r[49])-(flt(r[18])+flt(r[84]))) < 2e-7
        assert r[66] == 1 and r[5] >= 10
    assert a[67] == 1 and b[67] == 0
    assert max(flt(a[i]) for i in [69,72,75,78]) > 16
    assert max(flt(b[i]) for i in [69,72,75,78]) < 16
    retained = snapshots[retained_case][3,frame][slot]
    retired = snapshots[retired_case][3,frame][slot]
    assert retained[1] == 2 and retained[25] == 1 and retained[67] == 0
    assert retired[1] == retired[2] == 0
    assert key(frame,retained) == key(previous_frame,a)
    assert snapshots[retained_case][3,frame+1][slot][1] == 0
    return dict(stage=3, stageFrame=frame, slot=slot,
        retainedCase=retained_case, retiredCase=retired_case,
        sameBirthAndFamilyAndMotion=True, bothVmsAliveBeforeRetirement=True,
        sameDimensionsAndScale=True, rotationEqualsShotAnglePlusVmFloat0=True,
        differentRotationAndAngularVelocityRegister=True,
        retiredCaseQuadEntirelyAboveTop=True, retainedCaseQuadCrossesTop=True,
        retainedShotRetiresNextPlayer=True, animationFile=9, animationScript=6,
        sprite=29, drawingMode=1, originalPerSlotObserved=False)


retirements = [verify_retirement(216,1478,'late','baseline'),
               verify_retirement(234,2092,'baseline','late')]
a = snapshots['baseline'][3,1482][251]
b = snapshots['late'][3,1482][216]
assert a[1] == b[1] == 1 and a[5] == b[5] == 1
assert key(1482,a) == key(1482,b) and a[12:19] == b[12:19]
assert snapshots['baseline'][3,1482][216][1] == 0
matching = lambda rows: [r for r in rows if r[1] and key(1482,r)==key(1482,a) and r[12:19]==a[12:19]]
assert len(matching(snapshots['baseline'][3,1482])) == len(matching(snapshots['late'][3,1482])) == 1

# Decode only existing local ANM; emit identifiers/offsets, never its body.
sys.path.insert(0,str(R/'tools'))
anm = R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f/entries/pl00b.anm'
body = next(body for slot,_,body in importlib.import_module('th-anm-script-dump').scripts(raw(anm)) if slot==6)
assert struct.unpack_from('<hHhH',body,0x84) == (119,20,2,3)
assert struct.unpack_from('<3f',body,0x8c) == (10004.,10010.,10.)
assert struct.unpack_from('<hHhH',body,0x98) == (415,20,2,4)
assert struct.unpack_from('<3f',body,0xa0) == (0.,0.,10004.)
for name in ['ShotManager.cpp','ShotTh14.cpp','AnmInterpreter.cpp','AnmVm.cpp']:
    raw(R/'runtimes/th12/th12_web/cpp/game'/name)
for name in ['th14-build-shot-lifetime-observer-nov05.py','th14-run-shot-lifetime-nov05.py']:
    raw(R/'tools'/name)
native=read(H/'retail-component.json')
assert native['toolSha256']==SHA(raw(R/'tools/th14-shot-lifetime-native-nov05.py'))
assert native['passed'] and native['rotationOnlyControls']==4 and len(native['cases'])==10
assert not native['originalGameplayPerSlotObserved'] and not native['productionChanged']
assert all(x['retired']==x['expectedRetirement'] and x['releaseCalled']==x['retired'] for x in native['cases'])
assert all(x['quadMaxAbsError']==0 and x['quadBitIdentical'] for x in native['cases'] if not x['rotationSwapped'])
for name,item in native['evidenceBindings'].items():
    assert SHA(raw(R/name))==item['sha256']
for slot,frame in [(216,1478),(234,2092)]:
    for case in ['baseline','late']:
        pair=[x for x in native['cases'] if x['slot']==slot and x['stageFrame']==frame and x['case']==case]
        assert len(pair)==2 and pair[0]['retired']!=pair[1]['retired']
out = dict(schema='th14/shot-lifetime-public-evidence/1', runs=runs,
    fullSelectedTrajectoryTransparent=True, engineObjectsReused=141,
    matchedSnapshotPairs=55, slotsPerSnapshot=256, wordsPerSlot=96,
    countDifferences=count_differences, retirements=retirements,
    poolReuse=dict(stage=3,stageFrame=1482,baselineSlot=251,lateSlot=216,
        matchingUniqueActiveFamilyBirthAndMotion=True, globallyUniqueIdentityClaimed=False),
    script=dict(file=9,slot=6,randomDivisionOffset=132,angularVelocityOffset=152,
        randomReference=10010,divisor=10,wholeScriptUploaded=False),
    retailComponent=dict(cases=native['cases'],rotationOnlyControls=4,
        allSixUnswappedQuadsBitIdentical=True,wholeShotUpdateAndQuadExecuted=True,
        sinks=native['sinks'],executableSha256=native['executableSha256'],
        originalGameplayCapture=False),
    syntheticInitializeTimingControlOnly=True, originalPerSlotCompared=False,
    originalNineDifferencesClosed=False, productionChanged=False,
    ordinaryIndependentTimingAccepted=False, completeGame=False, nativeEquivalent=False,
    rawStatesAssetsSeedsOrBinariesUploaded=False, evidenceBindings=bindings,
    toolSha256=SHA(Path(__file__).read_bytes()))
target=R/'docs/porting/th14-shot-lifetime-nov05.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(verified=True,callbacksPerRun=35000,snapshotPairs=55,
    retirementCausesLocated=2,productionChanged=False,completeGame=False)))
