"""Verify native semantic camera copy order and integrate the checked Stage change."""
from pathlib import Path
import argparse,datetime,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-native-order-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify():
 bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 prep=load(H/'prepared.json');corepath=H/'build/ordinary/observer-build.json';core=load(corepath);source=Path(core['sourceSnapshotRoot'])
 assert core['all141CoreObjectsRecompiled']and len(core['objectBindings'])==141 and core['wasmSha256']==SHA(raw(corepath.parent/'observer.wasm'))
 for obj in core['objectBindings']:assert SHA(raw(Path(obj['path'])))==obj['sha256']
 for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert SHA(raw(source/name))==digest
 assert len(prep['changes'])==1 and prep['mappedDwords']==73 and prep['nativeProgressDwords']==75 and prep['unmappedNativeDwords']==[22,23]
 raw(R/'tools/th14-prepare-camera-native-order-nov04.py')
 native=load(H/'native.json');component=load(H/'component-verified.json')
 assert native['namedFieldMapping']and native['cases']==76 and native['referenceReadBlockExecutions']==456 and native['unmappedNativeByteOffsets']==[88,92]
 assert native['toolSha256']==SHA(raw(R/'tools/th14-camera-native-order-native-nov04.py'))
 assert component['verifiedNativeSemanticCameraOrder']and component['nativeProgressCases']==76 and component['semanticMappedWordsPerPrefix']==73 and component['failureCases']==9
 assert component['nativeProofSha256']==SHA(raw(H/'native.json'))and component['checkerSha256']==SHA(raw(R/'tools/th14-camera-native-order-check-nov04.mjs'))
 assert component['candidate']['wrongSemanticWords']==component['candidate']['wrongReferenceWords']==component['candidate']['wrongProgressCases']==0
 assert component['priorPublishedCoreControl']['wrongSemanticWords']==557 and component['priorPublishedCoreControl']['failedPrefixCases']==57 and component['priorPublishedCoreControl']['wrongProgressCases']==76
 builds={}
 for directory,key in [('component','candidate'),('component-prior','priorPublishedCoreControl')]:
  buildraw=raw(H/directory/'observer-build.json');build=json.loads(buildraw);builds[key]=build
  assert SHA(buildraw)==component[key]['buildSha256']and SHA(raw(H/directory/'observer.wasm'))==component[key]['wasmSha256']
  for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
  for obj in build['objectBindings']:assert SHA(raw(Path(obj['path'])))==obj['sha256']
 assert builds['candidate']['objectBindings']==core['objectBindings']and builds['candidate']['headerHashes']==builds['priorPublishedCoreControl']['headerHashes']
 assert [k for k in builds['candidate']['sourceHashes']if builds['candidate']['sourceHashes'][k]!=builds['priorPublishedCoreControl']['sourceHashes'][k]]==['th12_web/cpp/game/Stage.cpp']
 # Recheck actual retail instructions anchoring the semantic layout. No live launch.
 import importlib,sys
 if str(R/'tools')not in sys.path:sys.path.insert(0,str(R/'tools'))
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');layout=load(H/'layout-disassembly.json')
 assert SHA(image.data)==layout['originalExeSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 assert layout['nativeFovOffset']==84 and layout['nativeViewOffset']==96 and layout['nativeTargetOffset']==72
 for row in layout['anchors']:
  code=bytes.fromhex(row['bytes']);assert image.read(int(row['pc'],16),len(code))==code
 assert {x['field']:x['bytes']for x in layout['anchors']}['fov']=='f30f104154'
 assert {x['field']:x['bytes']for x in layout['anchors']}['view']=='8d7e60'
 sessionbuild=load(H/'session-component/observer-build.json');assert sessionbuild['objectBindings']==core['objectBindings']and sessionbuild['controlledSceneReadiness']
 assert SHA(raw(H/'session-component/observer.wasm'))==sessionbuild['wasmSha256']
 for name,digest in sessionbuild['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 modes=[]
 for mode in range(3):
  report=load(H/f'session-mode-{mode}/camera-word-session.json');v=report['values']
  assert report['verifiedControlledActualSessionCameraSceneBoundary']and report['cameraMode']==mode and report['wasmSha256']==sessionbuild['wasmSha256']
  assert report['driverSha256']==SHA(raw(R/'tools/th14-camera-word-session-check-nov04.mjs'))and not report['originalThreadScheduleAccepted']
  assert v[1:3]==[1,0]and v[4]==13 and v[7:9]==[1,2]and v[17]==1 and v[20]==0
  if mode==0:assert v[0]==v[18]==1 and v[5]==v[6]==0 and v[9]==5 and v[10]==v[13]==1 and v[19]==14 and report['controlledFailureAt']==0
  else:assert v[14:16]==[1,1]and v[16]==(4 if mode==1 else 8)and report['controlledFailureAt']>1
  modes.append(dict(mode=mode,callback=v[3],copiedWords=v[4],nextWordConfirmed=mode==0,loaderPhaseAtBoundary=v[9]if mode==0 else v[16]))
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
 stages=load(H/'stage-syntax/report.json');assert stages['passed']and len(stages['cases'])==4
 for item in stages['cases']:assert item['sourceSha256']==core['sourceHashes']['th12_web/cpp/game/Stage.cpp']
 app=load(H/'gles-two-stage/report.json');appbuild=load(H/'gles-build/build.json');refhome=R/'artifacts/th14/stage-object-snapshot-readiness-nov04/gles-two-stage';ref=load(refhome/'report.json')
 assert app['completed']and not app['error']and app['frames']==app['applicationTicks']==2289 and len(app['checks'])==27 and all(x['passed']for x in app['checks'])and app['physicalAudioDevicesOpened']==0
 assert appbuild['coreObjects']==core['objectBindings']and appbuild['coreWasmSha256']==core['wasmSha256']and appbuild['applicationCompiledAgainstFrozenCoreHeaders']
 assert appbuild['wasmSha256']==app['wasmSha256']==SHA(raw(H/'gles-build/application.wasm'))
 for name,binding in appbuild['sourceBindings'].items():
  b=raw(R/name);assert len(b)==binding['bytes']and SHA(b)==binding['sha256']
 assert app['captures']==ref['captures']and(app['pcmFrames'],app['pcmSha256'])==(ref['pcmFrames'],ref['pcmSha256'])
 for image in app['captures']:assert raw(H/'gles-two-stage'/image['file'])==raw(refhome/image['file'])
 browser=load(H/'browser/build.json');inputs=load(H/'browser/compile-inputs.json')
 assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and not browser['browserRun']and not browser['browserAcceptance']
 assert browser['wasmSha256']==SHA(raw(H/'browser/th14-sdl.wasm'))and browser['loaderSha256']==SHA(raw(H/'browser/th14-sdl.mjs'))
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
 protected={'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45','artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
 for name,digest in protected.items():assert SHA(raw(R/name))==digest
 report=dict(verifiedNativeSemanticCameraOrder=True,coreWasmSha256=core['wasmSha256'],freshCoreObjects=141,nativeProgressCases=76,mappedCameraDwords=73,nativePublicationDwords=75,unmappedNativeWordIndices=[22,23],opaqueWordsAreNotTrailing=True,opaqueWordsStillNotAccepted=True,nativeAnmReadBlockExecutions=456,cppSemanticWordsCompared=76*73,candidateWrongSemanticWords=0,priorPublishedCoreWrongSemanticWords=557,priorPublishedCoreFailedPrefixes=57,priorPublishedCoreWrongProgressCases=76,componentPublicationFailureCases=9,actualSessionCases=modes,finiteDefaultRecords=16,finiteDefaultCallbacks=callbacks,witnessedNormalVmCallbacks=35000,witnessedVmRows=1057,witnessedCombatCheckpoints=393,additionalSourceReadCallbacks=18000,sharedStageSyntaxChecks=4,applicationFrames=2289,applicationChecks=27,identicalReferenceImages=2,offlinePcmFrames=app['pcmFrames'],physicalAudioDevicesOpened=0,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],browserAcceptance=False,priorPrefixEvidenceHadNoSemanticLayoutValidation=True,oldRngFailureDifferences=old['differenceCounts'],oldRngFailureClosed=False,oldCameraFailureClosed=False,originalOldThreadScheduleRecovered=False,completeGame=False,nativeEquivalent=False,protectedFiles=protected,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 return report,prep,core,source
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integrate',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();report,prep,core,source=verify()
 if a.integrate:
  assert not(H/'integration.json').exists()
  for row in prep['changes']:assert SHA((R/'runtimes/th12'/row['path']).read_bytes())==row['beforeSha256']and SHA((source/row['path']).read_bytes())==row['afterSha256']
  for row in prep['changes']:
   target=R/'runtimes/th12'/row['path'];backup=H/'before-integration'/row['path'];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(target.read_bytes());target.write_bytes((source/row['path']).read_bytes());assert SHA(target.read_bytes())==row['afterSha256']
  prod=H/'production-core';prod.mkdir();(prod/'observer.wasm').write_bytes((H/'build/ordinary/observer.wasm').read_bytes());build=dict(core,productionIntegrated=True,rootProductionSourcesModified=True,sourcePublishedCommit=None,sourcePublicationPending=True,parentGameplayCorePublishedCommit='e08d4630fabf5e72aa0071aea7f4116800e3438e',productionChangedGameFiles=[x['path']for x in prep['changes']])
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
