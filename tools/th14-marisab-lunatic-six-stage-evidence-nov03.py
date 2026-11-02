"""Verify a bounded alternate Marisa B Lunatic six-stage recording; source EOF is not inferred."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-alternatives-nov03/case-marisab-lunatic';N=H/'native';bindings={};sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
end=load(H/'process-end.json');native=load(N/'report.json');model=load(H/'queue-end.json');quiet=load(H/'native-silence-verified.json');proof=load(H/'raw-verified.json');timing=load(H/'timing-verified.json');meta=load(H.parent/'marisab-lunatic-source.json');codec=load(H.parent/'native-codec-verified.json')
assert end['exitCode']==0 and end['guardStop'] is None and end['actualMastersZero'] and native['childExited'] and not native['error'] and native['callbacks']==81077 and native['recordedStages']==[1,2,3,4,5,6] and native['observedForcedReplayEndMenu']
assert not native['replayTerminalMarkerObservationImplemented'] and native['observedReplayTerminalMarker'] is None
assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==native['pid'] and all(all(s[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for s in quiet['samples'])
assert model['strictPassed'] and model['independentVerifierExitCode']==0 and model['nativeCallbacks']==81077 and model['nativeStages']==[1,2,3,4,5,6]
assert proof['verifiedFiniteEvidence'] and proof['callbacks']==81077 and proof['allSelected32Equal'] and proof['allCamera25Equal'] and proof['allHud2Equal'] and proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual'] and proof['vm303Rows']==1408 and proof['combatCheckpoints']==1074 and proof['orderedPublications']==1873
assert timing['passed'] and timing['reportedInputCoverageComplete'] and timing['verifierSha256']==sha(raw(R/'tools/th14-verify-native-initialize-timing-v2-nov03.py'))
assert codec['passed'] and meta['actualNativeCodecVerified'] and [s['stage'] for s in meta['stages']]==[1,2,3,4,5,6] and [meta['character'],meta['subtype'],meta['difficulty']]==[1,1,3]
assert native['sourceFullReplaySha256']==proof['sourceReplaySha256']==meta['sha256'] and sha(raw(N/'report.json'))==timing['nativeReportSha256']
for name,binding in proof['bindings'].items():assert sha((R/name).read_bytes())==binding['sha256'],name
build=load(R/'artifacts/th14/frame-rng-scope-nov02/counter-production-core/observer-build.json');assert proof['wasmSha256']==build['wasmSha256']=='f00a33cb9687fb544441d71bf9e5d78249b4d2e00d4059d59e7736ab1fb1c6eb'
raw(R/'tools/th14-verify-native-campaign-with-timing-nov03.py')
result={'verifiedFiniteMarisaBLunaticSixStages':True,'productionGameplayChanged':False,'coreCommit':'22c4f853fc1cb81b8a0c0891b88023f2f5dc065e','actualNativeCallbacks':81077,'observedStages':[1,2,3,4,5,6],'sourceReplayHeaderStages':[1,2,3,4,5,6],'sourceReplayEofProved':False,'stage6EntryProved':True,'observedForcedReplayEndMenu':True,'actualMastersZero':True,'strictAndIndependentPassed':True,'initializeTimingCoveragePassed':True,'vmRows':1408,'combatCheckpoints':1074,'initialPublications':1873,'naturalModeInventory':30,'allStageEntryModeInventory':28,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-marisab-lunatic-six-stage-nov03.json');a=p.parse_args();target=a.output.resolve();assert target.is_relative_to(R/'docs/porting') or target.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
