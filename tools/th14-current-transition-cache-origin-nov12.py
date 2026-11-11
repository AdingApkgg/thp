"""Compare retained current cache blocks with already-computed retail helpers.

No helper/game/GPU is rerun. A bit-exact candidate is not a copy timestamp.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/current-low-pause-transition-nov12'
N = R / 'artifacts/th14/low-pause-input-key-native-nov09/input-key-prefix'
P = R / 'artifacts/th14/current-gles-camera-provenance-v2-nov08'
bindings = {}


def read(p):
    b = p.read_bytes()
    bindings[p.relative_to(R).as_posix()] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return b


load = lambda p: json.loads(read(p))
q = load(H / 'qualified.json')
assert q['allChildrenWorkersHostsGpuAndClockRetired']
assert not q['rawDifferenceCounts']['state32'] and not q['slotDifferenceCounts']
assert q['firstRawDifferences']['camera75']['cppCallback'] == 14212
prior = load(P / 'verified.json')
prior_qualification = load(P / 'qualified.json')
assert prior_qualification['qualifiedFiniteProvenance']
assert prior['actualOriginalHelperCases'] == 2414 and prior['d3dxServiceExited']
assert prior['actualWindowsX86D3dxServices'] and not prior['exactPhysicalCopyTimestampRecovered']
inputs, outputs = read(P / 'inputs.u32'), read(P / 'outputs.u32')
assert hashlib.sha256(inputs).hexdigest() == prior['inputsSha256']
assert hashlib.sha256(outputs).hexdigest() == prior['outputsSha256']
assert len(inputs) == len(outputs) == 2414 * 300
cpp = read(H / 'current-prefix/observations.u32')
nb, nt = read(N / 'world-camera.raw'), read(N / 'world-camera-tail.u32')
native = lambda cb: nb[(cb-1)*292:cb*292] + nt[(cb-1)*8:cb*8]
cpp_camera = lambda cb: cpp[(cb-1)*456+132:(cb-1)*456+432]
pose = lambda raw: raw[:96] + raw[224:]
cb = 14212
assert pose(native(cb)) == pose(cpp_camera(cb))
cases = []
for owner, camera in [('native', native(cb)), ('currentCpp', cpp_camera(cb))]:
    target = camera[96:224]
    matches = [i for i in range(2414) if outputs[i*300+96:i*300+224] == target]
    candidates = []
    for index in matches:
        source = inputs[index*300:(index+1)*300]
        callbacks = [k for k in range(13900, cb) if pose(native(k)) == pose(source)]
        if callbacks:
            candidates.append(dict(retainedHelperCase=index,
                mode='screen' if index % 2 == 0 else 'perspective',
                poseCallbackCandidates=callbacks,
                sourcePoseSha256=hashlib.sha256(pose(source)).hexdigest()))
    assert matches and candidates
    cases.append(dict(owner=owner, cacheSha256=hashlib.sha256(target).hexdigest(),
        exactRetainedHelperMatches=len(matches), candidates=candidates))
assert cases[1]['exactRetainedHelperMatches'] == 1
assert cases[1]['candidates'][0]['poseCallbackCandidates'] == [14074]
assert cases[1]['candidates'][0]['mode'] == 'perspective'
assert all(c['mode'] == 'screen' for c in cases[0]['candidates'])
read(Path(__file__))
report = dict(recordedAt=datetime.now(timezone.utc).isoformat(),
    actualCurrentPrefixCallbacks=q['cppCallbacks'], firstDifferentCameraCallback=cb,
    comparedCacheWords=32, allNonCacheCameraWordsExact=True, cases=cases,
    finiteCandidateAnalysisOnly=True, physicalCopyTimestampRecovered=False,
    exactSourceWriterOrCrossThreadScheduleProven=False,
    recordedOriginalHelperCalculationsReusedNotRerun=True,
    noNewOriginalOsGameGpuAudioOrCppApplication=True,
    inheritedCacheDifferenceNotNormalized=True, strict113StillFails=True,
    productionChanged=False, completeGame=False, nativeEquivalent=False, bindings=bindings)
p = H / 'cache-origin.json'
assert not p.exists()
p.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(retainedNativeMathCandidatesFound=True,
    currentCppPerspectivePoseCandidate=14074, nativeScreenCandidates=True,
    physicalCopyTimestampRecovered=False, strict113StillFails=True)))
