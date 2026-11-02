"""Bind the retained TH14 seed-order hypothesis to private original evidence."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02';bindings={};sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
a=load(H/'retained-stack-context/verified.json');b=load(H/'retained-stack-context/seed-trajectory.json');c=load(H/'earliest-worker-experiment/independent-hypothesis-audit.json');audit=load(H/'initialize-time-audit.json');other=load(H/'retained-actor-experiment/summary.json')
assert a['passed'] and a['result']['objectIndex']==6 and len(a['tamperControls'])==4 and all(x['rejected'] for x in a['tamperControls'])
assert b['passed'] and b['originalNext32Executed']==11 and b['matchingStepCounts']=={'eventSeed':4,'portableSeed':7,'originalPlayerSeed':11} and not b['actualHistoricalCallCountsOrThreadOrderProved']
assert c['diagnosticDataIndependentlyChecked'] and c['callbacks']==36826 and c['selectedStateWordsEqual'] and c['camera25WordsEqual'] and c['hudWordsEqual'] and c['combatCheckpoints']==360 and c['combatWordsEqual'] and c['orderedPublications']==3834 and c['vmDifferingWords']==2 and not c['strictAcceptance'] and c['earlierInitializationTimeIsHypothesis'] and c['hypothesisRejectedByEventTimestampGate']
assert audit['passed'] and audit['verifiedNaturalCases']==16 and audit['nativeEventStreamMatchesRetainedReport'] and audit['unobservedEarlierTimeRejected']
assert other['candidateNotIntegrated'] and not other['oldFailureClosed']
for tool,expected in [('tools/th14-retained-stage3-stack-context-nov03.py',a['toolSha256']),('tools/th14-retained-seed-trajectory-nov03.py',b['toolSha256']),('tools/th14-earliest-worker-hypothesis-check-nov03.py',c['toolSha256'])]:assert sha(raw(R/tool))==expected
raw(R/'tools/th14-verify-native-initialize-timing-nov03.py');raw(R/'tools/th14-compare-earliest-worker-hypothesis-nov03.mjs');raw(R/'tools/th14-compare-retained-stage-actor-experiment-nov03.mjs')
for path,expected in [('artifacts/th14/reimu-controller-z-live-context-nov01/native/report.json',b['nativeReportSha256']),('artifacts/th14/frame-rng-scope-nov02/earliest-worker-experiment/model/report.json',c['modelReportSha256'])]:assert sha(raw(R/path))==expected
# Recheck event binding for all sixteen original/portable pairs.
case_count=0
for plan in sorted((H/'counter-regressions').glob('case-*/plan.json')):
 case=load(plan)['cases'][0];folder=plan.parent/case['key'];expected=load(folder/'initialize-time-verified.json')
 assert expected['passed'] and expected['verifierSha256']==sha((R/'tools/th14-verify-native-initialize-timing-nov03.py').read_bytes())
 assert sha(raw(R/case['native']/'report.json'))==expected['nativeReportSha256'] and sha(raw(folder/'model/report.json'))==expected['modelReportSha256'];case_count+=1
assert case_count==16
out={'verifiedFiniteStage3SeedOrderDiagnostic':True,'productionGameplayChanged':False,'retainedStageObjectIndex':6,'individualHistoricalVmIdentityProved':False,'retainedSeedTrajectoryOriginalNext32Instructions':11,'matchingTrajectoryCountsAreNotHistoricalOrderProof':True,'earlierTimeIsHypothesis':True,'hypothesisCallbacks':36826,'hypothesisStateCameraHudCombatAndPublicationsEqual':True,'combatCheckpoints':360,'publications':3834,'remainingVmZWordDifferences':2,'strictAcceptance':False,'timingGateRejectedHypothesis':True,'verifiedNaturalInitializeTimeCases':16,'exactHistoricalWorkerSeedStoreTimingProved':False,'newCoreFullApplicationAccepted':False,'browserAcceptance':False,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-stage3-seed-order-nov03.json');args=p.parse_args();target=args.output.resolve();assert target.is_relative_to(R/'docs/porting') or target.is_relative_to(H);data=(json.dumps(out,indent=2)+'\n').encode()
if args.check:assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
