"""Verify a terminal original Scene-copy TF observation; no campaign acceptance."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();native=args.native.resolve();build=args.build.resolve();bindings={}
    assert all(path.is_relative_to(ROOT/'artifacts/th14')for path in[native,build,args.plan.resolve()])
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    def lines(path):return[json.loads(line)for line in read(path).splitlines()if line]
    plan=load(args.plan.resolve());prepared=load(build/'prepared.json');report=load(native/'report.json')
    assert report['childExited']and not report['error']and not report['debugErrors']
    assert report['diagnosticPrefixOnly']and not report['fullReplayAccepted']and report['diagnosticStopReason']=='maximumCallbacks'
    assert report['callbacks']==plan['maximumCallbacks']==15000 and plan['maximumWallSeconds']==600
    assert not plan['automaticNextCase']and plan['originalCopyTrapFlagStepping']
    assert report['observerOptions']['maximum_callbacks']==15000 and report['observerOptions']['max_seconds']==600
    assert report['observerOptions']['scene_copy_word_events']and report['observerOptions']['scene_camera_events']
    assert report['observerOptions']['minimum_free_gib']==plan['minimumFreeGiB']==100
    assert report['observerOptions']['maximum_capture_gib']==plan['maximumCaptureGiB']==2
    assert report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
    assert report['hardwareDebugRegistersAndTrapFlagOnly']and not report['ordinaryMenuReplayInitialization']
    assert report['configuredMusicAndSoundVolumeZero']and not report['actualAudioPcmMeasured']
    assert report['observerTerminationRequested']and not report['observedForcedReplayEndMenu']
    assert report['sourceFullReplaySha256']==plan['intactReplaySha256']=='e98fc11baae2d58c9cdaee6a5f8f94e0504340eba6685c7187550168a415624f'
    frozen=read(native/'observer-source.py')
    assert SHA(frozen)==report['sourceSha256']==prepared['generatedObserverSha256']==plan['observerSha256']
    assert frozen==read(build/'observer.py')
    assert prepared['baseObserverSha256']==SHA(read(ROOT/prepared['baseObserverPath']))
    assert prepared['preparerSha256']==SHA(read(ROOT/'tools/th14-prepare-scene-copy-word-observer-oct26.py'))
    assert prepared['originalCopyTrapFlagStepping']and not prepared['changedOriginalInstructions']
    assert report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    camera=read(native/'world-camera.raw');assert len(camera)==15000*0x124 and SHA(camera)==report['worldCameraSha256']
    selected=read(native/'selected-state.u32');assert len(selected)==15000*128 and SHA(selected)==report['selectedSha256']
    assert sorted({struct.unpack_from('<I',selected,index*128+120)[0]for index in range(15000)})==[1,2]
    modules=load(native/'scene-copy-modules.json')
    assert modules==report['sceneCopyWordModules']and len(modules)==1
    assert modules[0]['name']=='d3dx9_43.dll'and modules[0]['sha256']=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
    copies=lines(native/'scene-camera-copy-events.jsonl');steps=lines(native/'scene-camera-copy-step-events.jsonl');words=lines(native/'scene-camera-word-copy-events.jsonl')
    assert SHA(read(native/'scene-camera-word-copy-events.jsonl'))==report['sceneCopyWordEventsSha256']
    assert len(words)==report['sceneCopyWordEvents']==3 and report['sceneCopyWordObserversRemaining']==0
    assert len(copies)==2 and copies[0]['event']=='scene-camera-copy-before'and copies[1]['event']=='scene-camera-copy-after'
    before,after=copies;assert before['stage']==after['stage']==2 and before['scene']==after['scene']
    assert before['pc']==0x40d435 and after['pc']==0x40d447 and before['threadId']==after['threadId']
    assert after['threeDestinationWordsObservedDirectly']and after['originalRepCopiedWords']==75
    assert len(steps)==after['originalCopyStepEvents']==78
    times=[before['hostMonotonicNs'],*[row['hostMonotonicNs']for row in steps],after['hostMonotonicNs']]
    assert all(left<=right for left,right in zip(times,times[1:]))
    assert [row['workerPc']for row in steps[:3]]==[0x40d43a,0x40d43f,0x40d445]
    assert [row['workerPc']for row in steps[3:]]==[0x40d445]*74+[0x40d447]
    for index,row in enumerate(steps):
        dr=row['debugRegisters'];regs=row['workerRegisters']
        assert row['readOnly']and row['threadId']==before['threadId']and row['scene']==before['scene']
        assert dr['dr6']&0x4000 and(dr['dr7']&~0x400)==0x0ddd0055
        assert[dr['dr0'],dr['dr1'],dr['dr2'],dr['dr3']]==[before['scene']+0x42a4+4*lane for lane in range(3)]+[0x40d447]
        if index>=2:
            count=index-2
            assert regs['ecx']==75-count and regs['esi']==0x4d9514+4*count
            assert regs['edi']==before['scene']+0x4274+4*count
            assert row['previousCopiedWords']==max(0,count-1)
    assert [row['word']for row in words]==[0,1,2]
    for lane,row in enumerate(words):
        step=steps[15+lane]
        assert row['workerRegisters']==step['workerRegisters']and row['debugRegisters']==step['debugRegisters']
        assert row['mainThreadRegisters']==step['mainThreadRegisters']
        assert row['exactTrapFlagStep']and row['actualOriginalRepIterationObserved']and row['readOnly']
        assert not row['nativeValuesProvidedToEngine']
        assert row['copiedWordHex']==after['copiedRightHex'][lane*8:lane*8+8]
        assert before['hostMonotonicNs']<row['hostMonotonicNs']<after['hostMonotonicNs']
        module=row['mainModule']
        if module is not None:assert module==modules[0]and row['mainModuleRva']==row['mainThreadRegisters']['eip']-module['base']
    prior=load(ROOT/'artifacts/th14/retail-sakuyab-easy-copy-word-prefix-hardware-oct26/report.json')
    assert prior['callbacks']==13578 and prior['childExited']and prior['error']=='AssertionError()'and prior['sceneCopyWordEvents']==1
    result=dict(verifiedFiniteOriginalSceneCopyObservation=True,diagnosticPrefixOnly=True,callbacks=15000,stagesObserved=[1,2],
        sceneCopiesObserved=1,exactCopyStepEvents=78,actualOriginalRepIterations=75,actualRightWordObservations=3,
        originalInstructionsUnmodified=True,configuredSilent=True,physicalPcmMeasured=False,
        debuggerPausesAffectTiming=True,mainThreadPcIsStoppedObservationNotSimultaneousCopyTimestamp=True,
        previousDataOnlyObservationFailedAndRetained=True,oldCameraFailureClosed=False,nativeValuesProvidedToEngine=False,
        originalOrdinaryMenuEquivalence=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        observerSha256=report['sourceSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Terminal15000-callback diagnostic prefix. Original75-dword copy observed with explicit TF stepping and configured hardware destination watches. Register/count sequencing and retained three right words are independently checked. Main PC is sampled after the debug event stops threads, not a simultaneous original memory-read timestamp. This cannot recover a previous real schedule, accept a full campaign, or certify ordinary original UI, pixels, audio or browser.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteOriginalSceneCopyObservation','callbacks','exactCopyStepEvents','actualOriginalRepIterations','actualRightWordObservations','oldCameraFailureClosed']}))


if __name__=='__main__':main()
