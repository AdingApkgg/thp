"""Qualify relative read-order diagnostics without promoting them to a scheduler fix."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[1]
Q=R/'artifacts/th14/relative-rng-camera-order-nov04'
T=R/'artifacts/th14/replay-rng-template-trace-nov04/native'
D=R/'artifacts/th14/camera-render-dimensions-nov04'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 bindings={}
 def raw(path):
  path=Path(path);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 def bind(records):
  for name,item in records.items():
   data=raw(R/name);assert len(data)==item['bytes'] and SHA(data)==item['sha256'],name
 def module(name):
  path=R/'tools'/name;raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 assert sys.byteorder=='little'
 inputs=load(Q/'inputs.json');bind(inputs['bindings'])
 assert inputs['verifierSha256']==SHA(raw(R/'tools/th14-relative-rng-camera-order-inputs-nov04.py'))
 assert inputs['verifiedRelativeRngRestoreOrderInputs'] and inputs['relativeReadOrderOnly'] and not inputs['exactInstructionScheduleRecovered']
 assert not inputs['nativeRngValuesProvidedToEngine'] and not inputs['originalMainVmIdentityObserved']
 rng_input=inputs['inputs'];camera_input=inputs['cameraInputs']
 assert rng_input==[dict(stage=3,callback=30837,resourcePumpNs=14339277224000,readyNs=14339279949300,point='firstScriptRngBeforeReadAfterResourcePump')]
 assert len(camera_input)==1 and camera_input[0]['point']==5 and camera_input[0]['ordinal']==1
 assert camera_input[0]['representativePointOnly'] and not camera_input[0]['originalExactSourceReadPcObserved']
 assert inputs['copiedRightRequiresNormalizedState'] and inputs['normalizationCompletionReceiptAfterCopyReceipt']
 generators=module('th14-prepare-relative-order-drivers-nov04.py')
 for kind,name in generators.FILES.items():assert raw(R/'tools'/name)==generators.source(kind)
 # Follow and bind the earlier generator chain rather than trusting checked-in driver text.
 for name in ['th14-prepare-render-dimensions-drivers-nov04.py','th14-prepare-full-camera-drivers-nov04.py']:raw(R/'tools'/name)
 core_bytes=raw(D/'build/ordinary/observer-build.json');core=json.loads(core_bytes)
 build=load(Q/'audit-build/observer-build.json')
 assert build['baseBuildSha256']==SHA(core_bytes) and build['objectBindings']==core['objectBindings']
 assert len(build['objectBindings'])==build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
 assert not build['rootProductionSourcesModified'] and not build['nativeValuesProvidedToEngine']
 for item in build['objectBindings']:assert SHA(raw(item['path']))==item['sha256']
 for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():assert SHA(raw(Path(build['sourceSnapshotRoot'])/name))==digest
 for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(name))==digest
 fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-relative-order-restore-audit-fixture-nov04.cpp'
 assert raw(fixture)==raw(build['fixtureGraphRoot'])
 assert build['buildToolSha256']==SHA(raw(R/'tools/th14-build-relative-order-restore-audit-nov04.py'))
 wasm=SHA(raw(Q/'audit-build/observer.wasm'));assert wasm==build['wasmSha256']=='53c43cc9badece2531159347ce59a29cd5a393a5d006d1194d567039c9425bf4'
 native_raw=raw(T/'selected-state.u32');native_camera=raw(T/'world-camera.raw')
 assert len(native_raw)==35000*32*4 and len(native_camera)==35000*73*4
 def counts(actual,expected,fields):
  av=memoryview(actual).cast('I');ev=memoryview(expected).cast('I');assert len(av)==len(ev)
  return {str(i):sum(a!=b for a,b in zip(av[i::fields],ev[i::fields]))for i in range(fields)if av[i::fields]!=ev[i::fields]}
 end=load(Q/'audit-comparisons/end.json');assert [x['case']for x in end['cases']]==['coarse','positive','after-seed-read','raw-right']
 expected_raw={'coarse':{'21':4137,'22':283,'26':1},'positive':{},'after-seed-read':{'21':4163,'22':307,'26':2},'raw-right':{}}
 expected_camera={'positive':{},'after-seed-read':{'63':52,'64':69},'raw-right':{'12':16701}}
 reports={};results=[]
 for case,terminal in zip(expected_raw,end['cases']):
  home=Q/'audit-comparisons'/case/'model';report=load(home/'report.json');full=load(home/'full-camera-report.json');reports[case]=report
  assert report['wasmSha256']==wasm and report['callbacks']==report['finalObservedCallbacks']==35000 and report['completed']
  kind='audit-coarse'if case=='coarse'else'audit'
  assert report['comparisonToolSha256']==SHA(raw(R/'tools'/generators.FILES[kind]))
  assert report['noRngSerialCounterHealthOrInputWrites'] and report['noPerFrameStateOverrides'] and not report['actualGpuOrAudio']
  assert report['relativeOrderInputs']['sha256']==SHA(raw(Q/'inputs.json'))
  assert report['relativeOrderInputs']['rng']==rng_input and report['relativeOrderInputs']['camera']==camera_input
  assert report['hostClockBoundaryReplayAdded']==(case!='coarse') and not report['ordinaryIndependentThreadTimingAcceptance']
  assert report['counterfactualRngAfterRead']==(case=='after-seed-read') and report['counterfactualCameraRaw']==(case=='raw-right')
  difference=counts(raw(home/'selected-state.u32'),native_raw,32);assert difference==report['differenceCounts']==expected_raw[case]
  camera_counts=counts(raw(home/'full-camera.u32'),native_camera[292:],73)
  assert full['firstCallback']==2 and full['callbacksCompared']==34999 and full['nativeWordIndices']==list(range(73))
  assert camera_counts==full['counts'] and full['portableSha256']==SHA(raw(home/'full-camera.u32'))
  if case in expected_camera:assert camera_counts==expected_camera[case]
  assert terminal['exitCode']==(0 if case=='positive'else 1) and terminal['guardStop']is None
  assert not report['completeGame'] and not report['nativeEquivalent']
  # Historical runner advisory incorrectly labelled coarse as replay-added. Preserve it,
  # and derive the authoritative result from source-bound model output and raw payloads.
  if case=='coarse':assert terminal['hostClockBoundaryReplayAdded']is True and report['coarseOrderControl']
  results.append(dict(case=case,exitCode=terminal['exitCode'],raw32DifferenceCounts=difference,camera73DifferenceCounts=camera_counts,hostClockBoundaryReplayAdded=report['hostClockBoundaryReplayAdded']))
 # The instrumented binary without relative deliveries must reproduce the shipped
 # ordinary negative: observing replay stores must not improve or perturb gameplay.
 coarse=Q/'audit-comparisons/coarse/model';prior=D/'old-rng-comparison/model'
 payloads=['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']
 payloads+=sorted(p.name for p in coarse.glob('portable-live-*.json'))
 payloads+=sorted(p.name for p in coarse.glob('portable-allocations-*.json'))
 for name in payloads:assert raw(coarse/name)==raw(prior/name),name
 # Interpret before-instruction native stops versus after-store production audit.
 stores=[x for x in map(json.loads,raw(T/'replay-rng-store-events.jsonl').splitlines())if x['stage']==3]
 assert [x['pc']for x in stores]==[0x45610f,0x456123,0x456129,0x456133]
 native_rng=[struct.unpack('<4I',bytes.fromhex(x['rngHex']))for x in stores]
 assert len({x[1]for x in native_rng})==1 and native_rng[0][1]==1579810
 wanted=[]
 for following,point in zip(native_rng[1:],[0,2,3]):wanted.append([3,30837,point,following[0]&65535,following[1],following[2]&65535,following[3]])
 for case in ['positive','after-seed-read','raw-right']:
  rows=[r for r in reports[case]['productionRngRestoreAudit']if r[0]==3]
  assert [r[:7]for r in rows]==wanted and all(r[9]==3 for r in rows)
 ordinary=[r for r in reports['coarse']['productionRngRestoreAudit']if r[0]==3]
 assert all(r[4]-native_rng[0][1]==22 for r in ordinary)
 positive=reports['positive'];assert positive['relativeRngReadOrderState'][:8]==[3,30837,1,0,3,7,1579810,213128]
 assert positive['relativeCameraReadOrderState']==[2,14182,1,5,14,1,0]
 proof=load(Q/'raw-verified.json');bind(proof['bindings'])
 assert proof['verifiedFiniteEvidence'] and proof['wasmSha256']==wasm and proof['callbacks']==35000
 assert proof['vm303Rows']==1072 and proof['combatCheckpoints']==480 and proof['nonemptyCombatCheckpoints']==49
 assert proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual'] and proof['allHud2Equal']
 assert proof['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-campaign.py'))
 rejection=load(Q/'scene-rejection.json');assert rejection['expectedRejection'] and rejection['exitCode']==1 and not rejection['whitelistChanged']
 assert rejection['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-scene-boundaries-nov03.py'))
 assert rejection['logSha256']==SHA(raw(Q/'scene-rejection.log')) and rejection['message']=='Unreviewed Scene scheduler driver'
 assert not (Q/'scene-rejection-output-must-not-exist.json').exists()
 protected={'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45','artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
 for name,digest in protected.items():assert SHA(raw(R/name))==digest
 return dict(verifiedRelativeReadOrderDiagnostic=True,callbacks=35000,selectedStateFields=32,cameraFields=73,cameraComparedWords=34999*73,
  vm303Rows=1072,combatCheckpoints=480,nonemptyCombatCheckpoints=49,allPositiveCapturedWordsEqual=True,
  sameBinaryCounterfactuals=results,wasmSha256=wasm,coreObjectsReused=141,productionGameplayCoreChanged=False,
  ordinaryControlPayloadsUnchanged=len(payloads),ordinaryRestoreScriptCallsLate=22,productionStoreLogicalFieldsMatchNative=True,
  originalVmIdentityIsNotInput=True,nativeRngValuesProvidedToEngine=False,hostClockBoundaryReplayAdded=True,
  cameraPointIsValueEquivalentRepresentative=True,originalExactSourceReadPcObserved=False,exactInstructionScheduleRecovered=False,
  strictSceneWhitelistUnchanged=True,strictSceneGateAccepted=False,oldDefaultFailureClosed=False,independentSchedulingAccepted=False,
  coarseRunnerAdvisoryFlagIncorrectAndPreserved=True,rawEvidenceGatePassed=True,nativeTrailingCameraWordsNotCaptured=[73,74],
  newOriginalCapturePerformed=False,physicalAudioDevicesOpened=0,browserUiAcceptance=False,completeGame=False,nativeEquivalent=False,
  protectedFiles=protected,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 result=verify();encoded=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode();out=a.output.resolve();assert out.is_relative_to(R)
 if a.check:assert out.read_bytes()==encoded
 else:assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(encoded)
 print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','protectedFiles','sameBinaryCounterfactuals']}))


if __name__=='__main__':main()
