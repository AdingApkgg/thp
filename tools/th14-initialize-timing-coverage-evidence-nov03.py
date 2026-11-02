"""Verify the bounded TH14 Initialize timing coverage and strict gate wrapper."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02';bindings={};sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
tests=load(H/'initialize-time-controls-rerun/report.json');wrapper=load(H/'strict-wrapper-control/verified.json');assert tests['passed'] and tests['naturalCases']==16 and len(tests['negativeControls'])==5 and all(x['rejected'] for x in tests['negativeControls']) and tests['noOriginalProcessLaunched'] and tests['physicalAudioDevicesOpened']==0
checker=R/'tools/th14-verify-native-initialize-timing-v2-nov03.py';testtool=R/'tools/th14-initialize-timing-controls-nov03.py';assert sha(raw(checker))==tests['verifierSha256'] and sha(raw(testtool))==tests['testToolSha256'];raw(R/'tools/th14-verify-native-campaign-with-timing-nov03.py')
assert wrapper['passed'] and wrapper['positiveFullStrictAndTimingPassed'] and wrapper['earlierHypothesisRejectedBeforeRawGate'];timing=load(H/'strict-wrapper-control/positive-timing.json');strict=load(H/'strict-wrapper-control/positive-raw.json');assert timing['passed'] and timing['reportedInputCoverageComplete'] and strict['verifiedFiniteEvidence'] and not strict['completeGame']
for name in tests['cases']:
 row=load(H/'initialize-time-controls-rerun'/(name+'.json'));assert row['passed'] and row['reportedInputCoverageComplete'] and row['verifierSha256']==tests['verifierSha256']
for case in tests['negativeControls']:
 folder=H/'initialize-time-controls-rerun'/case['name'];assert b'AssertionError' in raw(folder/'rejection.log') and not (folder/'must-not-pass.json').exists()
result={'verifiedFiniteInitializeTimeCoverage':True,'productionGameplayChanged':False,'strictCampaignWrapperAdded':True,'formalNaturalCases':16,'negativeControlsRejected':5,'positiveStrictAndTimingPassed':True,'hypothesisRejectedBeforeStrictGate':True,'onlyInitializeTimingCovered':True,'otherTimingAndFullGameProved':False,'completeGame':False,'nativeEquivalent':False,'bindings':bindings,'verifierSha256':sha(Path(__file__).read_bytes())}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-initialize-time-coverage-nov03.json');args=p.parse_args();target=args.output.resolve();assert target.is_relative_to(R/'docs/porting') or target.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if args.check:assert target.read_bytes()==data
else:target.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
