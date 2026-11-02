"""Verify a bounded original TH14 Normal scene-copy word observation, without inferring old timing."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-normal-word-probe';N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
def lines(p):return [json.loads(x) for x in raw(p).splitlines() if x]
report=load(N/'report.json');end=load(H/'process-end.json');plan=load(H/'plan.json');quiet=load(H/'native-silence-verified.json');prepared=load(R/'artifacts/th14/camera-interleaving-oct26/word-observer-build-v2/prepared.json')
assert report['childExited'] and not report['error'] and not report['debugErrors'] and end['exitCode']==0 and end['guardStop'] is None and end['actualMastersZero'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==report['pid']
assert report['diagnosticPrefixOnly'] and report['callbacks']==plan['maximumCallbacks']==15000 and report['diagnosticStopReason']=='maximumCallbacks' and report['observerTerminationRequested'] and not report['fullReplayAccepted'] and not report['observedForcedReplayEndMenu']
assert report['hardwareDebugRegistersAndTrapFlagOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
assert report['observerOptions']['scene_copy_word_events'] and report['observerOptions']['scene_camera_events'] and report['observerOptions']['controller_phase_events'] and plan['maximumCaptureMiB']==128 and plan['minimumFreeGiB']==100
assert report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert report['observerOptions']['maximum_callbacks']==15000 and report['observerOptions']['max_seconds']==900 and report['observerOptions']['minimum_free_gib']==100 and report['observerOptions']['maximum_capture_gib']==0.125
frozen=raw(N/'observer-source.py');assert sha(frozen)==report['sourceSha256']==prepared['generatedObserverSha256']=='709718618f3bd6bfbabb584ea062752820f44954402566fca39e306839db9801'
metadata=load(H.parent/'th14_ud07c1-source.json');assert metadata['actualNativeCodecVerified'] and metadata['expectedSelection']==[1,0,1] and report['sourceFullReplaySha256']==metadata['sha256']
source=raw(H.parent/'th14_ud07c1.rpy');decoded=raw(H.parent/'th14_ud07c1-decoded.bin');codec=load(H.parent/'native-codec-verified.json');assert sha(source)==metadata['sha256'] and sha(decoded)==metadata['decodedSha256'] and codec['passed']
codec_rows=[row for row in codec['rows'] if row['sha256']==metadata['sha256']];assert len(codec_rows)==1 and codec_rows[0]['decodedSha256']==metadata['decodedSha256'] and codec_rows[0]['nativeCodecObserverSha256']==codec['toolSha256']
assert list(struct.unpack_from('<3I',decoded,0x7c))==metadata['expectedSelection'] and [report['observerOptions'][k] for k in ['character','subtype','difficulty']]==metadata['expectedSelection']
selected=raw(N/'selected-state.u32');assert len(selected)==15000*128 and sha(selected)==report['selectedSha256'] and sorted({struct.unpack_from('<I',selected,i*128+120)[0] for i in range(15000)})==[1,2]
camera=raw(N/'world-camera.raw');assert len(camera)==15000*0x124 and sha(camera)==report['worldCameraSha256']
modules=load(N/'scene-copy-modules.json');assert modules==report['sceneCopyWordModules'] and len(modules)==1 and modules[0]['name']=='d3dx9_43.dll' and modules[0]['sha256']=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
copies=lines(N/'scene-camera-copy-events.jsonl');steps=lines(N/'scene-camera-copy-step-events.jsonl');words=lines(N/'scene-camera-word-copy-events.jsonl');assert len(copies)==2 and len(words)==report['sceneCopyWordEvents']==3 and len(steps)==78 and report['sceneCopyWordObserversRemaining']==0 and sha(raw(N/'scene-camera-word-copy-events.jsonl'))==report['sceneCopyWordEventsSha256']
before,after=copies;assert before['event']=='scene-camera-copy-before' and after['event']=='scene-camera-copy-after' and before['stage']==after['stage']==2 and before['pc']==0x40d435 and after['pc']==0x40d447 and before['threadId']==after['threadId'] and before['scene']==after['scene'] and after['threeDestinationWordsObservedDirectly'] and after['originalRepCopiedWords']==75 and after['originalCopyStepEvents']==78
times=[before['hostMonotonicNs'],*[row['hostMonotonicNs'] for row in steps],after['hostMonotonicNs']];assert all(left<=right for left,right in zip(times,times[1:]))
assert [row['workerPc'] for row in steps[:3]]==[0x40d43a,0x40d43f,0x40d445] and [row['workerPc'] for row in steps[3:]]==[0x40d445]*74+[0x40d447]
for index,row in enumerate(steps):
 dr=row['debugRegisters'];regs=row['workerRegisters'];assert row['readOnly'] and row['threadId']==before['threadId'] and row['scene']==before['scene']
 assert dr['dr6']&0x4000 and (dr['dr7']&~0x400)==0x0ddd0055 and [dr['dr0'],dr['dr1'],dr['dr2'],dr['dr3']]==[before['scene']+0x42a4+4*lane for lane in range(3)]+[0x40d447]
 if index>=2:
  count=index-2;assert regs['ecx']==75-count and regs['esi']==0x4d9514+4*count and regs['edi']==before['scene']+0x4274+4*count and row['previousCopiedWords']==max(0,count-1)
assert [x['word'] for x in words]==[0,1,2] and all(x['readOnly'] and x['exactTrapFlagStep'] and x['actualOriginalRepIterationObserved'] and not x['nativeValuesProvidedToEngine'] and x['threadId']==before['threadId'] and x['scene']==before['scene'] for x in words)
assert all(before['hostMonotonicNs']<x['hostMonotonicNs']<after['hostMonotonicNs'] for x in words)
for lane,row in enumerate(words):
 assert row['workerRegisters']==steps[15+lane]['workerRegisters'] and row['debugRegisters']==steps[15+lane]['debugRegisters'] and row['mainThreadRegisters']==steps[15+lane]['mainThreadRegisters'] and row['copiedWordHex']==after['copiedRightHex'][8*lane:8*lane+8]
 module=row['mainModule']
 if module is not None:assert module==modules[0] and row['mainModuleRva']==row['mainThreadRegisters']['eip']-module['base']
all_after=all((b:=x.get('lastMainCameraBoundary')) and b['event']=='world-perspective-right-written' and b['pc']==0x4465a6 and b['mainPhaseAtObservation']=='draw' and b['stage']==2 and b['precedingPlayerCallbacks']==x['precedingPlayerCallbacks'] and before['hostMonotonicNs']<b['hostMonotonicNs']<x['hostMonotonicNs'] for x in words)
result=dict(verifiedFiniteOriginalSceneCopyObservation=True,diagnosticPrefixOnly=True,callbacks=15000,observedStages=[1,2],stage=2,originalRepIterations=75,trapFlagStepEvents=78,rightWordObservations=3,allWordObservationsAfterMainPerspectiveBoundary=bool(all_after),actualMastersZero=True,debugExceptions=0,debuggerPausesAffectTiming=True,mainThreadPcIsStoppedObservationNotSimultaneousCopyTimestamp=True,oldNormalSixStageRunScheduleRecovered=False,oldCameraFailureClosed=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=H/'word-probe-verified.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(H) or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
