"""Verify a terminal Marisa A Normal original six-stage-entry capture if available."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-normal';N=H/'native';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
native=load(N/'report.json');terminal=load(H/'process-end.json');quiet=load(H/'native-silence-verified.json');comparison=load(H/'queue-end.json');metadata=load(H.parent/'th14_ud07c1-source.json');codec=load(H.parent/'native-codec-verified.json')
assert terminal['exitCode']==0 and terminal['guardStop'] is None and terminal['actualMastersZero'] and native['childExited'] and not native['error'] and not native['debugErrors'] and native['observedForcedReplayEndMenu']
assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==native['pid'] and all(all(s[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']) for s in quiet['samples'])
assert native['hardwareBreakpointsOnly'] and not native['instructionBytesPatched'] and not native['rngOrCounterWrites'] and not native['inputInjected'] and native['gameStateWordWrites']==1 and native['caseInitialization']['attractBitClearOnly']
assert metadata['actualNativeCodecVerified'] and metadata['expectedSelection']==[1,0,1] and codec['passed'] and native['sourceFullReplaySha256']==metadata['sha256'] and not native['replayTerminalMarkerObservationImplemented']
selected=raw(N/'selected-state.u32');count=native['callbacks'];assert len(selected)==count*128 and sha(selected)==native['selectedSha256'];stages=sorted({struct.unpack_from('<I',selected,i*128+120)[0] for i in range(count)});assert stages==native['recordedStages']==[1,2,3,4,5,6]
first=next(i+1 for i in range(count) if struct.unpack_from('<I',selected,i*128+120)[0]==6);assert first<count and any(struct.unpack_from('<I',selected,i*128+120)[0]==6 and struct.unpack_from('<I',selected,i*128)[0]>0 for i in range(count))
strict=comparison['strictPassed'];assert comparison['nativeCallbacks']==count and comparison['nativeStages']==stages
if strict:
 assert comparison['modelComparisonPassed'] and comparison['independentVerifierExitCode']==0
 exc=load(H/'exception-verified.json');timing=load(H/'timing-verified.json');proof=load(H/'raw-verified.json');assert exc['passed'] and timing['passed'] and proof['verifiedFiniteEvidence'] and proof['callbacks']==count and proof['allSelected32Equal'] and proof['allCamera25Equal'] and proof['allHud2Equal'] and proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual'];assert exc['nativeReportSha256']==timing['nativeReportSha256']==sha(raw(N/'report.json'))
 counts=dict(vmRows=proof['vm303Rows'],combatCheckpoints=proof['combatCheckpoints'],initialPublications=proof['orderedPublications'])
else:
 counts=None
gap=load(H/'gap-summary.json');assert gap['passedIndependentDifferenceCount'] and gap['callbacks']==count and not gap['selectedDifferenceCounts'] and gap['cameraDifferenceCounts']=={'12':16055} and gap['cameraFirst']['12']['index']==12165 and not gap['hudDifferenceCounts'] and gap['reportedVmValuesEqual'] and gap['reportedCombatWordsEqual'] and gap['vmAndCombatReportsNotIndependentlyRecomputedHere']
assert gap['nativeReportSha256']==sha(raw(N/'report.json')) and gap['modelReportSha256']==sha(raw(H/'model/report.json')) and gap['toolSha256']==sha(raw(R/'tools/th14-campaign-gap-summary-nov03.py'))
result=dict(verifiedFiniteMarisaANormalSixStageEntries=True,coreCommit='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e',callbacks=count,observedStages=stages,firstStage6Callback=first,actualMastersZero=True,debugExceptions=0,forcedReplayEndMenuObserved=True,sourceReplayEofProved=False,strictAndIndependentPassed=strict,strictCounts=counts,selectedStateIndependentlyEqual=True,hudIndependentlyEqual=True,cameraDifferenceCounts=gap['cameraDifferenceCounts'],cameraFirst=gap['cameraFirst'],vmAndCombatOnlyReportedEqual=True,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-marisaa-normal-six-stage-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
