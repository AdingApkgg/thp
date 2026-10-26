"""Recompute the Sakuya B Easy full capture failure and its observed copy window.

This checker certifies a retained failure; it never generates a full-run pass.
"""
import argparse
import array
import collections
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-sakuyab-easy-camera-failure-oct26.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=ROOT/'artifacts/th14/retail-sakuyab-easy-exact-camera-hardware-oct26'
    model=ROOT/'artifacts/th14/stage-item-retirement-oct25/sakuyab-easy-exact-camera-full-oct26'
    original,reported=load(native/'report.json'),load(model/'report.json');count=106903
    assert original['callbacks']==reported['callbacks']==count and original['recordedStages']==[1,2,3,4,5,6]
    assert original['observedForcedReplayEndMenu']and original['childExited']and not original['error']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['caseInitialization']['attractBitClearOnly']and original['gameStateWordWrites']==1 and not original['inputInjected']
    assert original['observerOptions']['camera_write_events']
    assert reported['noPerFrameStateOverrides']and reported['noNativePublicationValuesProvidedToEngine']
    selected=read(native/'selected-state.u32');assert len(selected)==count*128 and selected==read(model/'selected-state.u32')
    hud=read(native/'hud-score.u32');assert len(hud)==count*8 and hud==read(model/'portable-hud.u32')
    raw=read(native/'world-camera.raw');assert len(raw)==count*0x124
    offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected=array.array('I',(struct.unpack_from('<I',raw,frame*0x124+offset)[0]for frame in range(count)for offset in offsets))
    actual=array.array('I');actual.frombytes(read(model/'portable-camera.u32'));assert len(expected)==len(actual)==count*25
    differences=collections.Counter();first={}
    for index,(left,right)in enumerate(zip(expected,actual)):
        if left!=right:
            field=index%25;differences[field]+=1
            if field not in first:first[field]=dict(index=index//25,field=field,native=left,portable=right)
    assert dict(differences)=={12:36007,13:17176,14:17176}
    assert first=={12:dict(index=48170,field=12,native=3212771454,portable=3212836864),13:dict(index=48170,field=13,native=991688348,portable=0),14:dict(index=48170,field=14,native=3167345792,portable=0)}
    camera=load(model/'camera-report.json');assert camera['counts']=={str(k):v for k,v in differences.items()}and not camera['allCameraWordsEqual']
    stores_raw=read(native/'camera-right-write-events.jsonl');stores=[json.loads(line)for line in stores_raw.splitlines()]
    assert len(stores)==original['cameraRightWriteEvents']and SHA(stores_raw)==original['cameraRightWriteEventsSha256']
    assert all(row['ordinal']==index+1 and row['readOnly']and row['hardwareDataWrite']and row['watchAddress']==0x4d9544 and row['watchBytes']==4 and row['mainPhaseAtObservation']=='draw'for index,row in enumerate(stores))
    assert all(left['hostMonotonicNs']<right['hostMonotonicNs']for left,right in zip(stores,stores[1:]))
    scene=[json.loads(line)for line in read(native/'scene-camera-copy-events.jsonl').splitlines()]
    windows=[]
    for stage,callback in [(4,48006),(5,65260)]:
        before=next(row for row in scene if row['stage']==stage and row['event']=='scene-camera-copy-before')
        after=next(row for row in scene if row['stage']==stage and row['event']=='scene-camera-copy-after')
        assert before['pc']==0x40d435 and after['pc']==0x40d447 and before['threadId']==after['threadId']
        assert before['precedingPlayerCallbacks']==after['precedingPlayerCallbacks']==callback
        assert before['sourceRightHex']!=after['copiedRightHex']and before['hostMonotonicNs']<after['hostMonotonicNs']
        for row in [before,after]:
            store=row['lastMainCameraRightWrite'];assert store==stores[store['ordinal']-1]and store['hostMonotonicNs']<row['hostMonotonicNs']
        windows.append(dict(stage=stage,before=before,after=after))
    assert windows[0]['before']['mainThreadPcAtWorkerEvent']==0x446594 and windows[0]['after']['mainThreadPcAtWorkerEvent']==0x4465a6
    assert windows[1]['after']['mainThreadPcAtWorkerEvent']==0x446594
    frozen=read(native/'observer-source.py');assert SHA(frozen)==original['sourceSha256']
    other={name:load(model/file)[field]for name,file,field in [('animation','live-report.json','allLiveValuesEqual'),('combat','combat-snapshots.json','allCapturedCombatWordsEqual')]}
    assert all(other.values())
    result=dict(verifiedRetainedFailure=True,callbacks=count,stagesObserved=original['recordedStages'],naturalReplayEndObserved=True,allSelected32Equal=True,allHud2Equal=True,allCamera25Equal=False,cameraDifferenceCounts={str(k):v for k,v in differences.items()},firstCameraDifferences={str(k):v for k,v in first.items()},actualRightXStoreEvents=len(stores),copyWindows=windows,otherGatesReportedByComparator=other,fullRunPassed=False,noNativeValuesProvidedToEngine=True,wasmSha256=reported['wasmSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,completeGame=False,nativeEquivalent=False,scope='Independently recomputes selected32/HUD equality, all25 camera comparisons and two Scene copy windows with main-thread PCs and actual-store journal bindings. Animation/combat remain comparator reports here. Main-thread data-write breakpoints perturb scheduling. Does not infer exact per-component copy times, provide native values to the engine, waive camera fields or certify original ordinary UI/graphics/audio/browser equivalence.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(verifiedRetainedFailure=True,callbacks=count,cameraDifferenceCounts=result['cameraDifferenceCounts'],fullRunPassed=False)))


if __name__=='__main__':main()
