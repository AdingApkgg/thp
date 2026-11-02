"""Bind a read-only TH14 seed-store capture and GLES-only regression."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage3-worker-entry-vm-retry-nov03';N=H/'native';G=R/'artifacts/th14/shake-counter-applications-nov03';bindings={};sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
cap=load(H/'verified.json');comp=load(H/'independent-comparison-audit.json');quiet=load(H/'native-silence-verified.json');native=load(N/'report.json');audit=load(H/'observer-audit.json');assert cap['passed'] and cap['callbacks']==26000 and cap['workerStoreEvents']==2 and cap['unmatchedWorkerEvents']==2 and not cap['matchedStageObjectSnapshots']
assert cap['actualNativeMasterLevelsZero'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==native['pid'] and audit['sameProcessMutationCallSyntaxAsPriorObserver'];assert cap['nativeReportSha256']==sha(raw(N/'report.json')) and cap['eventSha256']==sha(raw(N/'seed-store-instruction-events.jsonl'))
assert comp['diagnosticDataIndependentlyChecked'] and comp['callbacks']==26000 and comp['selectedStateCameraHudAndCombatEqual'] and comp['combatCheckpoints']==341 and comp['orderedPublications']==3835 and comp['vmRowsCompared']==720 and comp['vmDifferingWords']==7
assert comp['twoTimingChoicesProduceEqualCheckedPayloads'] and comp['baselineTimingGateAccepted'] and comp['postStoreCompositeTimingGateRejected'] and not comp['strictAcceptance'] and not comp['actualHistoricalOtherCaptureOrderProved']
assert comp['nativeReportSha256']==sha(raw(N/'report.json')) and comp['modelReportSha256']==sha(raw(H/'compare-baseline/model/report.json')) and comp['secondModelReportSha256']==sha(raw(H/'compare-seed-store/model/report.json'))
assert cap['toolSha256']==sha(raw(H/'verify-observer.py')) and comp['toolSha256']==sha(raw(R/'tools/th14-observed-seed-store-comparison-nov03.py'))
assert audit['observerSha256']==sha(raw(R/'tools/th14-stage3-worker-entry-vm-observer-nov03.py')) and sha(raw(N/'observer-source.py'))==native['sourceSha256']==audit['observerSha256']
raw(R/'tools/th14-compare-observed-seed-store-nov03.mjs');raw(R/'tools/th14-verify-native-initialize-timing-nov03.py')
proof=load(G/'gles-single-verified.json');assert proof['verifiedFiniteSingleBackendApplicationFullReplay'] and not proof['verifiedCurrentShakeCounterApplicationsFullReplay'] and proof['backends']==['gles'] and proof['sourceCommit']=='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e' and proof['framesPerBackend']==122622 and proof['assertionsPerBackend']==45 and proof['physicalAudioDevicesOpened']==0
for name,binding in proof['bindings'].items():assert sha((R/name).read_bytes())==binding['sha256'],name
verifier=R/'tools/th14-shake-counter-application-full-evidence-nov03.py';assert sha(raw(verifier))==proof['verifierSha256']
assert not proof['ordinaryOriginalGuiAccepted'] and not proof['originalWholePixelsOrPcmAccepted'] and not proof['independentSchedulingAccepted'] and not proof['browserAcceptance']
out={'verifiedFiniteSeedStoreCaptureAndGles':True,'productionGameplayChanged':False,'coreCommit':'22c4f853fc1cb81b8a0c0891b88023f2f5dc065e','nativeDiagnosticCallbacks':26000,'nativeObservedWorkerSeedStoreBoundaries':2,'nativeMatchedStageObjectAtStore':0,'nativeMusicAndEffectsMasterLevelsZero':True,'nativeDebuggerPausesAffectTiming':True,'comparisonsCallbacks':26000,'comparisonCombatCheckpoints':341,'comparisonOrderedPublications':3835,'comparisonVmRows':720,'comparisonVmDifferingZWords':7,'bothTimingChoicesSameCheckedPayloads':True,'postStoreCompositeCompletionNotProved':True,'strictPrefixAccepted':False,'glesFrames':122622,'glesAssertions':45,'glesFullActuallyExecuted':True,'glesIndependentlyVerified':True,'glesOnlyNotDualBackend':True,'physicalAudioDevicesOpenedByGles':0,'webgpuFullAccepted':False,'old36826HistoricalOrderProved':False,'browserAcceptance':False,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-observed-seed-store-gles-nov03.json');args=p.parse_args();target=args.output.resolve();assert target.is_relative_to(R/'docs/porting') or target.is_relative_to(H);data=(json.dumps(out,indent=2)+'\n').encode()
if args.check:assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
