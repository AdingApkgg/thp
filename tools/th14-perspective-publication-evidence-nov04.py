"""Verify perspective publication boundaries with actual x86 D3DX and bounded regressions."""
from pathlib import Path
import argparse,datetime,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/perspective-publication-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify():
 bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 prep=load(H/'prepared.json');corepath=H/'build/ordinary/observer-build.json';core=load(corepath);source=Path(core['sourceSnapshotRoot'])
 assert core['all141CoreObjectsRecompiled']and len(core['objectBindings'])==141 and core['wasmSha256']==SHA(raw(corepath.parent/'observer.wasm'))
 for obj in core['objectBindings']:assert SHA(raw(Path(obj['path'])))==obj['sha256']
 for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert SHA(raw(source/name))==digest
 assert len(prep['changes'])==4 and prep['nativePerspectiveBoundaries']==6 and prep['matrixInternalStoresNotModeled']
 assert prep['preparerSha256']==SHA(raw(R/'tools/th14-prepare-perspective-publication-nov04.py'))
 native=load(R/'artifacts/th14/perspective-publication-native-cpu-nov04/verified.json')
 assert native['verifiedOriginalPerspectiveBoundariesAndWorkerCopy']and native['actualWindowsX86D3dxServices']and native['dllServicesDelegatedToActualReferenceCpu']and native['unicornD3dxFloatingExecutionRejected']
 assert native['mainPerspectiveExecutions']==4 and native['workerCopyExecutions']==24 and len(native['rows'])==24 and len(native['serviceRequests'])==12
 assert native['toolSha256']==SHA(raw(R/'tools/th14-perspective-publication-native-cpu-nov04.py'))
 assert native['serviceSourceSha256']==SHA(raw(R/'tools/th14-perspective-d3dx-worker-nov04.cs'))
 assert native['serviceExeSha256']==SHA(raw(R/'artifacts/th14/perspective-publication-native-cpu-nov04/d3dx-worker.exe'))
 component=load(H/'component-cpu-comparison.json');rejected=load(H/'component-comparison.json')
 assert component['verifiedOriginalPerspectiveComponent']and component['wrongWords']==0 and component['comparedMappedWords']==1752 and component['failureCases']==24
 assert component['nativeProofSha256']==SHA(raw(R/'artifacts/th14/perspective-publication-native-cpu-nov04/verified.json'))
 assert component['checkerSha256']==SHA(raw(R/'tools/th14-perspective-publication-component-cpu-check-nov04.mjs'))
 assert not rejected['verifiedOriginalPerspectiveComponent']and rejected['wrongWords']==66 and rejected['componentBuildSha256']==component['componentBuildSha256']and rejected['componentWasmSha256']==component['componentWasmSha256']
 buildraw=raw(H/'component/observer-build.json');build=json.loads(buildraw)
 assert SHA(buildraw)==component['componentBuildSha256']and SHA(raw(H/'component/observer.wasm'))==component['componentWasmSha256']and build['objectBindings']==core['objectBindings']
 for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 scope=load(H/'scope-verified.json');scopebuild=load(H/'scope-component/observer-build.json')
 assert scope['verifiedPerspectiveScopeProtocol']and scope['cases']==6 and scopebuild['objectBindings']==core['objectBindings']
 assert scope['wasmSha256']==scopebuild['wasmSha256']==SHA(raw(H/'scope-component/observer.wasm'))and scope['checkerSha256']==SHA(raw(R/'tools/th14-perspective-scope-check-nov04.mjs'))
 for name,digest in scopebuild['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 sessionbuild=load(H/'session-component/observer-build.json');assert sessionbuild['objectBindings']==core['objectBindings']and sessionbuild['controlledSceneReadiness']
 assert SHA(raw(H/'session-component/observer.wasm'))==sessionbuild['wasmSha256']
 for name,digest in sessionbuild['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 modes=[]
 for mode in range(3):
  report=load(H/f'session-mode-{mode}/perspective-session.json');v=report['values']
  assert report['verifiedControlledActualSessionPerspectiveSceneBoundary']and report['cameraMode']==mode and report['wasmSha256']==sessionbuild['wasmSha256']
  assert report['driverSha256']==SHA(raw(R/'tools/th14-perspective-session-check-nov04.mjs'))and not report['originalThreadScheduleAccepted']
  assert v[1:3]==[1,0]and v[4]==4 and v[7:9]==[1,2]and v[17]==1 and v[20]==0
  if mode==0:assert v[0]==v[18]==1 and v[5]==v[6] and v[9]==5 and v[10]==v[13]==1 and v[19]==5 and report['controlledFailureAt']==0
  else:assert v[14]==1 and v[15]==(0 if mode==1 else 1)and v[16]==(4 if mode==1 else 8)and report['controlledFailureAt']>1
  modes.append(dict(mode=mode,callback=v[3],perspectivePoint=v[4],nextPerspectivePointConfirmed=mode==0,loaderPhaseAtBoundary=v[9]if mode==0 else v[16]))
 regression=load(H/'current-modes/end.json');assert regression['casesCompleted']==17 and regression['strictV4Passes']==regression['newModelRuns']==16
 callbacks=0
 for case in regression['cases']:
  if not case['strictV4Passed']:assert case['key']=='reimub-easy'and case['reportedDebugExceptions']==12;continue
  proof=load(H/'current-modes'/case['key']/'raw-verified.json');assert proof['verifiedFiniteEvidence']and proof['wasmSha256']==core['wasmSha256']
  callbacks+=proof['callbacks']
  for name,binding in proof['bindings'].items():
   b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 assert callbacks==1379760
 witness=load(H/'public-observed-run/raw-verified.json');assert witness['verifiedFiniteEvidence']and witness['callbacks']==35000 and witness['vm303Rows']==1057 and witness['combatCheckpoints']==393
 for name,binding in witness['bindings'].items():
  b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 assert load(H/'public-observed-run/correct-gates/scene.json')['observedVmInputContract']['verifiedObservedVmInputContract']
 stages=load(H/'perspective-syntax/report.json');assert stages['passed']and len(stages['cases'])==8
 for item in stages['cases']:assert item['sourceSha256']==core['sourceHashes']['th12_web/cpp/game/'+item['source']]
 app=load(H/'gles-two-stage/report.json');appbuild=load(H/'gles-build/build.json');refhome=R/'artifacts/th14/stage-object-snapshot-readiness-nov04/gles-two-stage';ref=load(refhome/'report.json')
 assert app['completed']and not app['error']and app['frames']==app['applicationTicks']==2289 and len(app['checks'])==27 and all(x['passed']for x in app['checks'])and app['physicalAudioDevicesOpened']==0
 assert appbuild['coreObjects']==core['objectBindings']and appbuild['coreWasmSha256']==core['wasmSha256']and appbuild['applicationCompiledAgainstFrozenCoreHeaders']
 assert appbuild['wasmSha256']==app['wasmSha256']==SHA(raw(H/'gles-build/application.wasm'))
 for name,binding in appbuild['sourceBindings'].items():
  b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 assert app['captures']==ref['captures']and(app['pcmFrames'],app['pcmSha256'])==(ref['pcmFrames'],ref['pcmSha256'])
 for image in app['captures']:assert raw(H/'gles-two-stage'/image['file'])==raw(refhome/image['file'])
 browser=load(H/'browser-v2/build.json');inputs=load(H/'browser-v2/compile-inputs.json')
 assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and not browser['browserRun']and not browser['browserAcceptance']
 assert browser['wasmSha256']==SHA(raw(H/'browser-v2/th14-sdl.wasm'))and browser['loaderSha256']==SHA(raw(H/'browser-v2/th14-sdl.mjs'))
 assert inputs['frozenCoreBuildSha256']==SHA(raw(corepath))and inputs['frozenCoreWasmSha256']==core['wasmSha256']
 for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert inputs['sourceBindings'][name]['sha256']==digest
 oldhome=H/'old-rng-comparison';old=load(oldhome/'model/report.json');assert not load(oldhome/'end.json')['strictAndIndependentPassed']and old['wasmSha256']==core['wasmSha256']and old['differenceCounts']=={'21':4137,'22':283,'26':1}
 sourceproof=load(H/'source-read-comparison/raw-verified.json');assert sourceproof['verifiedFiniteEvidence']and sourceproof['callbacks']==18000 and sourceproof['wasmSha256']==core['wasmSha256']
 assert load(H/'source-read-comparison/end.json')['strictAndIndependentPassed']
 for name,binding in sourceproof['bindings'].items():
  data=raw(R/name);assert len(data)==binding['bytes']and SHA(data)==binding['sha256']
 for gate in ['exceptions','timing','scene']:assert load(H/'source-read-comparison'/(gate+'.json'))['passed']
 for gate in ['exceptions','timing']:assert load(H/'public-observed-run/correct-gates'/(gate+'.json'))['passed']
 assert load(H/'public-observed-run/end.json')['exitCode']==0 and load(H/'application-end.json')['exitCode']==0
 diagnostics=load(H/'controlled-clock-verified.json')
 assert diagnostics['verifiedControlledCombinedClockExperiment']and diagnostics['allExpandedCapturedCameraWordsEqual']and diagnostics['expandedCameraWords']==2484929
 assert not diagnostics['strictNativeCampaignAccepted']and not diagnostics['originalScheduleRecovered']and not diagnostics['defaultOriginalRngFailureClosed']and not diagnostics['defaultOriginalCameraFailureClosed']
 assert diagnostics['verifierSha256']==SHA(raw(R/'tools/th14-rng-perspective-clock-evidence-nov04.py'))
 for name,binding in diagnostics['bindings'].items():
  data=raw(R/name);assert len(data)==binding['bytes']and SHA(data)==binding['sha256']
 oldcamera=load(oldhome/'model/camera-report.json');assert oldcamera['counts']=={'12':16701}
 protected={'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45','artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
 for name,digest in protected.items():assert SHA(raw(R/name))==digest
 report=dict(verifiedPerspectivePublication=True,coreWasmSha256=core['wasmSha256'],freshCoreObjects=141,nativePerspectiveProfiles=4,perspectiveBoundaries=6,nativeWorkerCopies=24,mappedCameraWordsCompared=1752,wrongMappedWords=0,unicornFloatingOracleRejectedWrongWords=66,actualWindowsX86D3dxServicesUsed=True,scopeProtocolCases=6,componentFailureCases=24,actualSessionCases=modes,finiteDefaultRecords=16,finiteDefaultCallbacks=callbacks,witnessedNormalVmCallbacks=35000,witnessedVmRows=1057,witnessedCombatCheckpoints=393,additionalSourceReadCallbacks=18000,sharedCameraSessionSyntaxChecks=8,applicationFrames=2289,applicationChecks=27,identicalReferenceImages=2,offlinePcmFrames=app['pcmFrames'],physicalAudioDevicesOpened=0,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],browserAcceptance=False,controlledCombinedClockCases=diagnostics['matchingRawPayloadCases'],controlledExpandedCameraWords=2484929,controlledExpandedCameraFields=71,controlledTimingIsNotOriginalSchedule=True,strictContractRejectedControlledDriver=True,oldRngFailureDifferences=old['differenceCounts'],oldCameraFailureDifferences=oldcamera['counts'],oldRngFailureClosed=False,oldCameraFailureClosed=False,originalOldThreadScheduleRecovered=False,matrixInternalStoresNotModeled=True,unmappedNativeWordIndices=[22,23],opaqueWordsStillNotAccepted=True,completeGame=False,nativeEquivalent=False,protectedFiles=protected,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 return report,prep,core,source
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integrate',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();report,prep,core,source=verify()
 if a.integrate:
  assert not(H/'integration.json').exists()
  for row in prep['changes']:assert SHA((R/'runtimes/th12'/row['path']).read_bytes())==row['beforeSha256']and SHA((source/row['path']).read_bytes())==row['afterSha256']
  for row in prep['changes']:
   target=R/'runtimes/th12'/row['path'];backup=H/'before-integration'/row['path'];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(target.read_bytes());target.write_bytes((source/row['path']).read_bytes());assert SHA(target.read_bytes())==row['afterSha256']
  prod=H/'production-core';prod.mkdir();(prod/'observer.wasm').write_bytes((H/'build/ordinary/observer.wasm').read_bytes());build=dict(core,isolatedPrototypeOnly=False,productionIntegrated=True,rootProductionSourcesModified=True,sourcePublishedCommit=None,sourcePublicationPending=True,parentGameplayCorePublishedCommit='acc1b44e5ef3415d6b92790fe671b837a94ceb33',productionChangedGameFiles=[x['path']for x in prep['changes']])
  (prod/'observer-build.json').write_bytes((json.dumps(build,indent=2)+'\n').encode());(H/'integration.json').write_bytes((json.dumps(dict(integrated=True,changedFiles=prep['changes'],evidence=report,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n').encode())
 report['productionIntegrated']=(H/'integration.json').exists()
 if report['productionIntegrated']:
  for row in prep['changes']:assert SHA((R/'runtimes/th12'/row['path']).read_bytes())==row['afterSha256']
 if a.output:
  path=a.output.resolve();assert path.is_relative_to(R)
  if a.check:assert json.loads(path.read_bytes())==report
  else:assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps({k:v for k,v in report.items()if k not in('bindings','protectedFiles')}),flush=True)
if __name__=='__main__':main()
