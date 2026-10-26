"""Recompute the retained Sakuya B Lunatic camera failure, without waiving it."""
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
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-sakuyab-lunatic-camera-window-oct26.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=ROOT/'artifacts/th14/retail-sakuyab-lunatic-exit-boundary-hardware-oct26'
    model=ROOT/'artifacts/th14/stage-item-retirement-oct25/sakuyab-lunatic-exit-boundary-full-oct26'
    original,reported=load(native/'report.json'),load(model/'report.json');count=126882
    assert original['callbacks']==reported['callbacks']==count and original['recordedStages']==[1,2,3,4,5,6]
    assert original['observedForcedReplayEndMenu'] and original['childExited'] and not original['error']
    assert original['hardwareBreakpointsOnly'] and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['caseInitialization']['attractBitClearOnly'] and original['gameStateWordWrites']==1 and not original['inputInjected']
    assert reported['noPerFrameStateOverrides'] and reported['noNativePublicationValuesProvidedToEngine']
    selected=read(native/'selected-state.u32');assert len(selected)==count*128 and selected==read(model/'selected-state.u32')
    hud=read(native/'hud-score.u32');assert len(hud)==count*8 and hud==read(model/'portable-hud.u32')
    raw=read(native/'world-camera.raw');assert len(raw)==count*0x124
    offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected=array.array('I',(struct.unpack_from('<I',raw,frame*0x124+offset)[0]for frame in range(count)for offset in offsets))
    actual=array.array('I');actual.frombytes(read(model/'portable-camera.u32'));assert len(expected)==len(actual)==count*25
    differences=collections.Counter();first=None
    for index,(left,right)in enumerate(zip(expected,actual)):
        if left!=right:
            differences[index%25]+=1
            if first is None:first=dict(index=index//25,field=index%25,native=left,portable=right)
    assert dict(differences)=={12:16631} and first==dict(index=14463,field=12,native=3212836864,portable=0)
    camera=load(model/'camera-report.json');assert camera['counts']=={'12':16631} and not camera['allCameraWordsEqual']
    scene=[json.loads(line)for line in read(native/'scene-camera-copy-events.jsonl').decode().splitlines()]
    before=next(row for row in scene if row['stage']==2 and row['event']=='scene-camera-copy-before')
    after=next(row for row in scene if row['stage']==2 and row['event']=='scene-camera-copy-after')
    assert before['pc']==0x40d435 and after['pc']==0x40d447 and before['threadId']==after['threadId']
    assert before['precedingPlayerCallbacks']==after['precedingPlayerCallbacks']==14352
    assert before['sourceRightHex']=='000000000000000000000000' and after['copiedRightHex']=='000080bf0000000000000000'
    boundaries=[json.loads(line)for line in read(native/'camera-boundary-events.jsonl').decode().splitlines()]
    assert not any(before['hostMonotonicNs']<row['hostMonotonicNs']<after['hostMonotonicNs']for row in boundaries)
    following=next(row for row in boundaries if row['hostMonotonicNs']>after['hostMonotonicNs'])
    assert following['event']=='world-perspective-right-written' and following['pc']==0x4465a6
    prefix=ROOT/'artifacts/th14/retail-sakuyab-lunatic-camera-write-prefix-hardware-oct26'
    prefix_native=load(prefix/'report.json')
    prefix_verified=load(ROOT/'artifacts/th14/stage-item-retirement-oct25/sakuyab-lunatic-camera-write-prefix-verified-oct26.json')
    assert prefix_native['callbacks']==20000 and prefix_native['childExited'] and not prefix_native['error'] and not prefix_native['observedForcedReplayEndMenu']
    assert prefix_native['instructionBytesPatched']==prefix_native['rngOrCounterWrites']==0 and prefix_native['observerOptions']['camera_write_events']
    assert prefix_verified['diagnosticPrefixOnly'] and prefix_verified['callbacks']==20000 and not prefix_verified['originalNaturalReplayEndObserved']
    assert all(prefix_verified[key]for key in ['allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual'])
    frozen=read(prefix/'observer-source.py');assert SHA(frozen)==prefix_native['sourceSha256']==SHA(read(ROOT/'tools/th14-native-campaign-observer-oct25.py'))
    stores_raw=read(prefix/'camera-right-write-events.jsonl');stores=[json.loads(line)for line in stores_raw.splitlines()]
    assert SHA(stores_raw)==prefix_native['cameraRightWriteEventsSha256'] and len(stores)==prefix_native['cameraRightWriteEvents']==3739
    assert len({row['threadId']for row in stores})==1
    assert all(row['ordinal']==index+1 and row['readOnly'] and row['hardwareDataWrite'] and row['watchAddress']==0x4d9544 and row['watchBytes']==4 and row['mainPhaseAtObservation']=='draw'for index,row in enumerate(stores))
    assert all(left['hostMonotonicNs']<right['hostMonotonicNs']for left,right in zip(stores,stores[1:]))
    prefix_scene=[json.loads(line)for line in read(prefix/'scene-camera-copy-events.jsonl').decode().splitlines()]
    assert len(prefix_scene)==2
    for row in prefix_scene:
        write=row['lastMainCameraRightWrite'];assert write==stores[write['ordinal']-1] and write['hostMonotonicNs']<row['hostMonotonicNs'] and row['mainThreadPcAtWorkerEvent']>0
    assert prefix_scene[0]['sourceRightHex']==prefix_scene[1]['copiedRightHex']
    prefix_summary=dict(diagnosticPrefixOnly=True,callbacks=20000,naturalReplayEndObserved=False,allSelectedObservedGatesEqual=True,vm303Rows=prefix_verified['vm303Rows'],combatCheckpoints=prefix_verified['combatCheckpoints'],nonemptyCombatCheckpoints=prefix_verified['nonemptyCombatCheckpoints'],actualRightXStores=len(stores),storePcCounts={hex(pc):number for pc,number in collections.Counter(row['pc']for row in stores).items()},reproducedOldCopyInterleaving=False,oldFullRunFailureClosed=False)
    result=dict(verifiedRetainedFailure=True,callbacks=count,stagesObserved=original['recordedStages'],naturalReplayEndObserved=True,allSelected32Equal=True,allHud2Equal=True,allCamera25Equal=False,cameraDifferenceCounts={str(key):value for key,value in differences.items()},firstCameraDifference=first,sceneCopyWindow=dict(before=before,after=after,nextReportedPerspectiveBoundary=following,noPostCallCameraBoundaryRecordedBetweenMarkers=True),failureRemainsRequired=True,noNativeValuesProvidedToEngine=True,wasmSha256=reported['wasmSha256'],comparisonToolSha256=reported['comparisonToolSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,completeGame=False,nativeEquivalent=False,scope='Independently recomputes the retained selected32/HUD equality, camera failure and coarse Scene-copy observations. Does not generate a full-run pass, infer an exact missing write time, certify other reported gates or prove ordinary gameplay/GPU/PCM/browser equivalence.')
    result['cameraWriteDiagnosticPrefix']=prefix_summary
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(verifiedRetainedFailure=True,callbacks=count,cameraField=12,differentCallbacks=16631,fullRunPassed=False)))


if __name__=='__main__':main()
