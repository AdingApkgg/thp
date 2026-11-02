"""Verify a finite TH14 Hard prefix with exception, timing-v3 and raw gates."""
from pathlib import Path
import argparse,ast,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-alternatives-nov03/case-marisaa-hard-exception-probe';N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
r=load(N/'report.json');end=load(H/'process-end.json');quiet=load(H/'native-silence-verified.json');summary=load(H/'exception-summary.json');model=load(H/'model-end.json');exc=load(H/'exception-verified.json');timing=load(H/'timing-v3-verified.json');proof=load(H/'raw-verified.json')
assert r['callbacks']==31200 and r['recordedStages']==[1,2] and r['diagnosticPrefixOnly'] and r['observerTerminationRequested'] and r['childExited'] and not r['error'] and not r['debugErrors'] and not r['observedForcedReplayEndMenu']
assert end['exitCode']==1 and end['guardStop'] is None and end['actualMastersZero'] and quiet['nativePid']==r['pid'] and quiet['verifiedActualNativeMasterLevelsZero'] and summary['debugExceptions']==0 and not summary['oldExceptionResolved']
assert r['hardwareBreakpointsOnly'] and not r['instructionBytesPatched'] and not r['rngOrCounterWrites'] and not r['inputInjected'] and r['gameStateWordWrites']==1 and r['caseInitialization']['attractBitClearOnly']
assert model['combinedGatePassed'] and model['modelExitCode']==model['combinedGateExitCode']==0 and model['vmRows']==3489 and model['combatCheckpoints']==164 and model['initialPublications']==2457
assert exc['passed'] and exc['debugExceptionCount']==0 and timing['passed'] and timing['firstObservedStage']==1 and timing['activeLaterStages']==[2]
assert exc['nativeReportSha256']==timing['nativeReportSha256']==sha(raw(N/'report.json')) and timing['modelReportSha256']==sha(raw(H/'model/report.json'))
assert proof['verifiedFiniteEvidence'] and proof['callbacks']==31200 and proof['vm303Rows']==3489 and proof['combatCheckpoints']==164 and proof['orderedPublications']==2457 and proof['allSelected32Equal'] and proof['allCamera25Equal'] and proof['allHud2Equal'] and proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual']
for name,b in proof['bindings'].items():assert sha((R/name).read_bytes())==b['sha256'],name
src=raw(R/'tools/th14-exception-diagnostic-observer-nov03.py');base=raw(R/'tools/th14-stage3-seed-store-observer-v2-nov01.py');assert sha(src)==r['sourceSha256']=='8fff454266b7765874ab2c238ad6d46b1d4afca95c0e63557b7373d99e97b6b0'
def calls(s,name):return [ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(s)) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr==name]
for name in ['WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext']:assert calls(src,name)==calls(base,name)
assert exc['verifierSha256']==sha(raw(R/'tools/th14-verify-native-debug-exceptions-nov03.py')) and timing['verifierSha256']==sha(raw(R/'tools/th14-verify-native-initialize-timing-v3-nov03.py'))
result=dict(verifiedFiniteCleanHardPrefix=True,coreCommit='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e',callbacks=31200,observedStages=[1,2],debugExceptions=0,actualMastersZero=True,exceptionTimingAndRawGatesPassed=True,vmRows=3489,combatCheckpoints=164,initialPublications=2457,priorExceptionNotReproducedOrExplained=True,stage3RaceNotObservedInThisPrefix=True,sourceReplayEofProved=False,debuggerPausesAffectTiming=True,nativeValuesProvidedToEngine=False,originalInstructionsPatched=False,productionChanged=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-hard-clean-exception-prefix-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
