"""Audit retained TH14 Hard transition windows; timing hypotheses do not prove a run."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-alternatives-nov03/case-marisaa-hard';N=H/'native';bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def load(p):return json.loads(raw(p))
def lines(p):return [json.loads(x) for x in raw(p).splitlines() if x]
native=load(N/'report.json');baseline=load(H/'gap-audit.json');after=load(H/'after-hypothesis-audit.json');combined=load(H/'camera-seed-hypothesis-audit.json');quiet=load(H/'native-silence-verified.json')
assert native['callbacks']==75855 and native['recordedStages']==[1,2,3,4,5] and native['childExited'] and not native['error'] and native['observedForcedReplayEndMenu']
assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==native['pid']
assert baseline['passedGapAudit'] and baseline['selectedDifferenceCounts']=={'21':1,'24':1} and baseline['cameraDifferenceCounts']=={'12':22137,'13':22137,'14':22137} and not baseline['strictPassed']
assert after['passedHypothesisAudit'] and not after['cameraDifferenceCounts'] and after['selectedDifferenceCounts']==baseline['selectedDifferenceCounts'] and after['observedInitializeTimingCoveragePassed']
assert combined['passedHypothesisAudit'] and not combined['cameraDifferenceCounts'] and not combined['selectedDifferenceCounts'] and combined['initializeTimingValidatorRejected'] and not combined['observedInitializeTimingCoveragePassed']
selected=raw(N/'selected-state.u32');times=raw(N/'player-host-monotonic.u64');assert len(selected)==75855*128 and len(times)==75855*8
row=lambda i:struct.unpack_from('<32I',selected,i*128)
time=lambda i:struct.unpack_from('<Q',times,i*8)[0]
i=31382;prior=row(i-1);current=row(i);assert prior[30]==current[30]==3 and prior[24]==340745 and current[24]==0 and current[21]==38667
transitions=lines(N/'transition-events.jsonl');sleep=next(e for e in transitions if e['event']=='sleep60-returned' and e['stage']==3);later=next(e for e in transitions if e['event']=='replay-seeds-restored-before-globals-copy' and e['stage']==3)
assert sleep['returnInstructionObservedDirectly'] and sleep['pc']==0x435b11 and later['pc']==0x456133 and later['originalInstructionBytes'].startswith('f3a5')
assert time(i-1)<sleep['hostMonotonicNs']<time(i)<later['hostMonotonicNs'] and (struct.unpack('<4I',bytes.fromhex(later['rngHex']))[0]&0xffff)==current[21] and struct.unpack('<4I',bytes.fromhex(later['rngHex']))[3]==0
copies=lines(N/'scene-camera-copy-events.jsonl');before=next(e for e in copies if e['stage']==4 and e['event']=='scene-camera-copy-before');after_event=next(e for e in copies if e['stage']==4 and e['event']=='scene-camera-copy-after');draw=after_event['lastMainCameraBoundary']
assert before['readOnly'] and after_event['readOnly'] and draw['readOnly'] and before['pc']==0x40d435 and after_event['pc']==0x40d447 and draw['pc']==0x4465a6 and before['threadId']==after_event['threadId'] and before['precedingPlayerCallbacks']==after_event['precedingPlayerCallbacks']==draw['precedingPlayerCallbacks']==48482
assert before['hostMonotonicNs']<draw['hostMonotonicNs']<after_event['hostMonotonicNs'] and before['sourceRightHex']==draw['rightHex']==after_event['copiedRightHex']
model=load(H/'model-camera-seed-hypothesis/report.json');phase=next(x for x in model['observedPhaseInputs'] if x['stage']==3 and x['phase']=='Initialize');assert phase['readyNs']==sleep['hostMonotonicNs'] and phase['completionSource']=='counterfactualEarliestSleepReturnNotObservedInitialize'
checker=R/'tools/th14-verify-native-initialize-timing-v2-nov03.py';raw(checker)
proc=subprocess.run([sys.executable,'-X','utf8',str(checker),'--native',str(N),'--model',str(H/'model-camera-seed-hypothesis'),'--output',str(H/'camera-seed-hypothesis-should-not-exist.json')],capture_output=True);assert proc.returncode!=0 and b'AssertionError' in proc.stderr and not (H/'camera-seed-hypothesis-should-not-exist.json').exists()
result=dict(verifiedRetainedTransitionWindows=True,coreCommit='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e',callbacks=75855,observedStages=[1,2,3,4,5],sourceReplayEofProved=False,forcedEndMenuObserved=True,actualMastersZero=True,baselineSelectedMismatchCounts=baseline['selectedDifferenceCounts'],baselineCameraMismatchCounts=baseline['cameraDifferenceCounts'],callbackWithRestoredScriptSeedAndZeroGameplayCalls=i+1,playerSnapshotAfterSleepReturnBefore456133=True,priorPlayerGameplayCalls=prior[24],laterPlayerGameplayCalls=current[24],seedValueUsedAsEngineInput=False,exactEarlierStoreOrderDirectlyObserved=False,sceneCopyStartsBeforeAndEndsAfterPerspectiveBoundary=True,sceneCopyWordOrderDirectlyObserved=False,counterfactualCameraPayloadEqual=True,counterfactualCombinedPayloadEqual=True,combinedInitializeTimingValidatorRejected=True,combinedSampledVmRows=combined['sampledVmRowsEqual'],combinedCombatCheckpoints=combined['combatCheckpointsEqual'],combinedInitialPublications=combined['initialPublicationsEqual'],hypothesesAcceptedAsNativeSchedule=False,productionChanged=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-hard-transition-window-nov03.json');args=p.parse_args();output=args.output.resolve();assert output.is_relative_to(R/'docs/porting') or output.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if args.check:assert output.read_bytes()==data
else:output.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
