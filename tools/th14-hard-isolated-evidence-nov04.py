"""Verify one exception-free Hard capture and retain its strict camera failure."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-hard-isolated'
N=H/'native'
bindings={}
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def read(path):
    raw=path.read_bytes()
    bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
    return raw

def load(path):
    return json.loads(read(path))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    n=load(N/'report.json');end=load(H/'process-end.json');q=load(H/'queue-end.json')
    quiet=load(H/'native-silence-verified.json');gap=load(H/'gap-summary.json')
    assert end['exitCode']==0 and end['guardStop']is None and end['actualMastersZero']
    assert n['childExited'] and not n['error'] and not n['debugErrors']
    assert n['observedForcedReplayEndMenu'] and n['hardwareBreakpointsOnly']
    assert not n['instructionBytesPatched'] and not n['rngOrCounterWrites'] and not n['inputInjected']
    assert n['gameStateWordWrites']==1 and n['caseInitialization']['attractBitClearOnly']
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==n['pid']
    assert all(all(s[k]==0 for k in ('musicConfig','effectsConfig','musicMaster','effectsMaster')) for s in quiet['samples'])
    source=read(N/'observer-source.py')
    assert sha(source)==n['sourceSha256']==sha(read(R/'tools/th14-native-campaign-observer-oct25.py'))
    meta=load(H.parent/'th14_ud0552-source.json');codec=load(H.parent/'native-codec-verified.json')
    assert codec['passed'] and meta['actualNativeCodecVerified']
    assert meta['sha256']==n['sourceFullReplaySha256']==sha(read(H.parent/'th14_ud0552.rpy'))
    assert sha(read(H.parent/'th14_ud0552-decoded.bin'))==meta['decodedSha256']
    selected=read(N/'selected-state.u32');count=n['callbacks']
    assert count==114842 and len(selected)==count*128 and sha(selected)==n['selectedSha256']
    first={};active={};last=1
    for i in range(count):
        words=struct.unpack_from('<32I',selected,i*128)
        assert list(words[27:30])==[1,0,2]
        stage=words[30];assert last<=stage<=6;last=stage
        first.setdefault(stage,i+1)
        if words[0]>0:active.setdefault(stage,i+1)
    assert sorted(first)==sorted(active)==n['recordedStages']==[1,2,3,4,5,6]
    assert q['nativeCallbacks']==count and not q['strictPassed'] and not q['modelComparisonPassed']
    assert gap['passedIndependentDifferenceCount'] and gap['callbacks']==count
    assert gap['nativeReportSha256']==sha(read(N/'report.json'))
    assert gap['modelReportSha256']==sha(read(H/'model/report.json'))
    assert gap['toolSha256']==sha(read(R/'tools/th14-campaign-gap-summary-nov03.py'))
    assert not gap['selectedDifferenceCounts'] and not gap['hudDifferenceCounts']
    assert gap['cameraDifferenceCounts']=={'12':24286,'13':24286}
    assert all(gap['cameraFirst'][k]['index']==90556 for k in ('12','13'))
    assert gap['reportedVmValuesEqual'] and gap['reportedCombatWordsEqual']
    scene=[json.loads(x)for x in read(N/'scene-camera-copy-events.jsonl').splitlines()]
    before,after=[x for x in scene if x['stage']==6]
    assert before['event']=='scene-camera-copy-before' and after['event']=='scene-camera-copy-after'
    assert before['precedingPlayerCallbacks']==after['precedingPlayerCallbacks']==90413
    assert before['mainPhaseAtObservation']==after['mainPhaseAtObservation']=='draw'
    assert before['hostMonotonicNs']<after['hostMonotonicNs']
    assert before['sourceRightHex']!=after['copiedRightHex']
    result=dict(verifiedFiniteHardIsolatedCapture=True,callbacks=count,debugExceptions=0,
        observedStages=sorted(first),firstStageEntryCallbacks=first,firstActiveStageCallbacks=active,
        allSixEntriesInOneExceptionFreeCapture=True,actualMastersZero=True,
        forcedReplayEndMenuObserved=True,sourceReplayEofProved=False,strictPassed=False,
        selected32AndHudIndependentlyEqual=True,cameraDifferenceCounts=gap['cameraDifferenceCounts'],
        firstCameraDifferentCallback=90557,cameraCopyAtCallback=90413,
        sourceRightBeforeDiffersFromCopiedRightAfter=True,
        vmAndCombatOnlyReportedEqual=True,oldHardExceptionCauseResolved=False,
        mainDrawLabelProvesExactCopyOrder=False,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    target=R/'docs/porting/th14-hard-isolated-nov04.json'
    raw=(json.dumps(result,indent=2)+'\n').encode()
    if a.check:assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))

if __name__=='__main__':main()
