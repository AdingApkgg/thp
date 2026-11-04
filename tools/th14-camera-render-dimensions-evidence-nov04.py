"""Verify the integrated render-size fields, finite regressions and remaining gaps."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-render-dimensions-nov04'
N=R/'artifacts/th14/unified-event-context-trace-nov04'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 def bind_recorded(records):
  for name,binding in records.items():
   data=raw(R/name);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
 def module(name):
  path=R/'tools'/name;raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 assert sys.byteorder=='little'
 prepared=load(H/'prepared.json');integration=load(H/'integration.json');assert integration['productionIntegrated'] and integration['sourceFilesChanged']==4
 normalizations={item['path']:item for item in integration.get('publicationLineEndingNormalization',[])}
 assert len(prepared['changes'])==4 and prepared['sourcePreparationToolSha256']==SHA(raw(R/'tools/th14-prepare-camera-render-dimensions-nov04.py'))
 for item in prepared['changes']:
  assert SHA(raw(Path(prepared['sourceRoot'])/item['path']))==item['afterSha256']
  published_path=R/'runtimes/th12'/item['path'];published=raw(published_path)
  normalization=normalizations.get(published_path.relative_to(R).as_posix())
  if normalization:
   compiled=raw(Path(prepared['sourceRoot'])/item['path'])
   assert normalization['compiledSourceSha256']==item['afterSha256'] and SHA(published)==normalization['publishedSourceSha256']
   assert b'R"'not in compiled and compiled.replace(b'\r\n',b'\n')==published and b'\r\n'not in published
  else:assert SHA(published)==item['afterSha256']
  assert SHA(raw(H/'before-integration'/Path(item['path']).name))==item['beforeSha256']
 for name,digest in integration['protectedFiles'].items():assert SHA(raw(R/name))==digest
 raw(R/'tools/th14-build-camera-render-dimensions-nov04.py')
 core_path=H/'build/ordinary/observer-build.json';core=load(core_path);assert core['all141CoreObjectsRecompiled'] and core['sessionLayoutChanged']
 assert core['wasmSha256']=='b4595e3e7f008cd7f096c4e2ca9c5dcd1d2971ea4d5178e5f6c2317dba89b9f9'
 assert SHA(raw(core_path.parent/'observer.wasm'))==core['wasmSha256']
 recovery=load(H/'build/metadata-failure.json');assert recovery['ordinaryWasmBeforeRecoverySha256']==core['wasmSha256']
 assert core['objectsCompiledAfterMetadataRecovery']==0 and len(recovery['objects'])==141
 for item in core['objectBindings']:assert SHA(raw(Path(item['path'])))==item['sha256']
 for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert SHA(raw(Path(core['sourceSnapshotRoot'])/name))==digest
 for item in (H/'prepared-before-stage-size-assertion.json',H/'prepared-before-session-metadata.json'):raw(item)
 assert (H/'build-stage-size-assertion-failure').is_dir()
 component=load(H/'component-verified.json');assert component['verifiedAllCameraWordMapping'] and component['wrongWords']==0 and component['comparedPrefixWords']==5700
 assert component['mappedWordsPerPrefix']==75 and component['resetDimensionWords']==64 and component['failureCases']==9 and not component['unmappedNativeWordIndices']
 for tool,key in [('th14-camera-all-words-check-nov04.mjs','checkerSha256')]:assert SHA(raw(R/'tools'/tool))==component[key]
 native=load(H/'all-words-native.json');dimension=load(H/'reference/native.json')
 assert SHA(raw(H/'all-words-native.json'))==component['nativePrefixProofSha256'] and SHA(raw(H/'reference/native.json'))==component['nativeDimensionProofSha256']
 assert native['all75CameraWordsMapped'] and native['referenceReadBlockExecutions']==456 and dimension['screenMatrixMathSkipped'] and not dimension['fullCameraResetAccepted']
 for tool,proof in [('th14-camera-all-words-native-nov04.py',native),('th14-camera-render-dimensions-native-nov04.py',dimension)]:assert SHA(raw(R/'tools'/tool))==proof['toolSha256']
 build=load(H/'component/observer-build.json');assert SHA(raw(H/'component/observer.wasm'))==build['wasmSha256']==component['wasmSha256']
 for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 strict=load(H/'current-modes/end.json');assert strict['casesCompleted']==17 and strict['strictV4Passes']==16 and strict['sourceWasmSha256']==core['wasmSha256']
 valid_strict={};strict_callbacks=0
 for case in strict['cases']:
  if case.get('notRunOnCurrentCore'):
   assert case['key']=='reimub-easy' and case['reportedDebugExceptions']==12;continue
  assert case['strictV4Passed'] and case['model']['exitCode']==case['verifier']['exitCode']==0
  proof=load(H/'current-modes'/case['key']/'raw-verified.json');assert proof['verifiedFiniteEvidence'] and proof['wasmSha256']==core['wasmSha256']
  bind_recorded(proof['bindings'])
  for gate in ('exceptions','timing','scene'):assert load(H/'current-modes'/case['key']/(gate+'.json'))['passed']
  valid_strict[case['key']]=case;strict_callbacks+=case['callbacks']
 assert strict_callbacks==1379760
 drivers=module('th14-prepare-render-dimensions-drivers-nov04.py')
 for kind,name in drivers.NAMES.items():assert raw(R/'tools'/name)==drivers.driver_source(kind)
 for name in ['th14-prepare-full-camera-drivers-nov04.py','th14-prepare-mode-perspective-window-driver-nov04.py','th14-prepare-observed-perspective-window-driver-nov04.py']:raw(R/'tools'/name)
 mixed=load(H/'mixed-73-field-regressions/end.json');plan=load(H/'mixed-73-field-regressions/plan.json');assert mixed['casesCompleted']==17 and mixed['expandedPasses']==16 and mixed['mixedHostBoundaryDiagnostics']
 indices=list(range(73));total_words=0;diagnostic_records=0;cases=[]
 for case,record in zip(plan['cases'],mixed['cases']):
  assert case['key']==record['key'];key=case['key']
  if record.get('notRun'):assert key=='reimub-easy' and record['exceptions']==12;continue
  assert record['exitCode']==0 and record['guardStop']is None and key in valid_strict
  home=H/'mixed-73-field-regressions'/key/'model';report=load(home/'report.json');full=load(home/'full-camera-report.json');native_home=R/case['native']
  selected_build=H/('mode-window-component'if record['legacyWindowDiagnostic']else'full-camera-component')/'observer-build.json';build=load(selected_build)
  assert SHA(raw(selected_build))==record['buildSha256'] and SHA(raw(selected_build.parent/'observer.wasm'))==build['wasmSha256']==report['wasmSha256']
  for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
  assert report['comparisonToolSha256']==record['driverSha256'] and full['nativeWordIndices']==indices and full['comparedFieldsPerCallback']==73 and not full['opaqueNativeWordIndicesNotAccepted']
  assert report['observedPhaseInputs']==load(H/'current-modes'/key/'model/report.json')['observedPhaseInputs']
  if record['legacyWindowDiagnostic']:
   assert report['legacyWindowDiagnosticOnly'] and not report['strictSceneContractAccepted'] and report['legacyPerspectiveWindows'];diagnostic_records+=1
   prior=load(R/'artifacts/th14/mode-perspective-window-diagnostic-nov04/cases'/key/'model/report.json')
   assert report['legacyPerspectiveWindows']==prior['legacyPerspectiveWindows'] and report['legacyWindowStates']==prior['legacyWindowStates']
  else:assert not report.get('addedMeasuredHostClockBoundary')
  names=['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']
  names+=sorted(p.name for p in home.glob('portable-live-*.json'));names+=sorted(p.name for p in home.glob('portable-allocations-*.json'))
  for name in names:assert raw(home/name)==raw(H/'current-modes'/key/'model'/name)
  assert raw(home/'selected-state.u32')==raw(native_home/'selected-state.u32')
  count=record['callbacks'];actual_raw=raw(home/'full-camera.u32');actual=memoryview(actual_raw).cast('I');expected=memoryview(raw(native_home/'world-camera.raw')).cast('I')
  assert len(actual)==(count-1)*73 and len(expected)==count*73 and not full['counts'] and full['allExpandedCapturedWordsEqual']
  assert SHA(actual_raw)==full['portableSha256'] and full['callbacksCompared']==count-1
  for frame in range(1,count):assert actual[(frame-1)*73:frame*73]==expected[frame*73:(frame+1)*73],(key,frame+1)
  words=(count-1)*73;total_words+=words;cases.append(dict(key=key,callbacks=count,fields=73,comparedWords=words,wrongWords=0,legacyWindowDiagnostic=record['legacyWindowDiagnostic']))
 assert diagnostic_records==12 and len(cases)==16 and total_words==100721312
 complete=H/'complete-source-comparison';assert load(complete/'end.json')['exitCode']==0
 report=load(complete/'model/report.json');full=load(complete/'model/full-camera-report.json');source=load(complete/'model/observed-source-camera.json')
 source_build=load(H/'source-window-component/observer-build.json');assert SHA(raw(H/'source-window-component/observer.wasm'))==source_build['wasmSha256']==report['wasmSha256']
 for name,digest in source_build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 assert report['comparisonToolSha256']==SHA(drivers.driver_source('source-window')) and report['allRaw32ByteIdentical']
 assert full['callbacksCompared']==34999 and full['nativeWordIndices']==indices and full['allExpandedCapturedWordsEqual'] and not full['counts']
 actual=memoryview(raw(complete/'model/full-camera.u32')).cast('I');expected=memoryview(raw(N/'native/world-camera.raw')).cast('I')
 assert len(actual)==34999*73
 for frame in range(1,35000):assert actual[(frame-1)*73:frame*73]==expected[frame*73:(frame+1)*73]
 reads=[json.loads(line)for line in raw(N/'native/worker-camera-source-read-events.jsonl').splitlines()];read=next(x for x in reads if x['stage']==source['sourceStage'])
 assert source['sourceEventSequence']==read['debugEventSequence']==48784 and source['sourceCallback']==read['precedingPlayerCallbacks']==30787
 clock=load(N/'verified.json');assert clock['verifierSha256']==SHA(raw(R/'tools/th14-unified-event-context-evidence-nov04.py'));bind_recorded(clock['bindings'])
 witnessed_window=load(N/'perspective-window-verified.json');assert report['measuredPerspectiveWindows']==witnessed_window['windows']
 journal=next(json.loads(line)for line in raw(N/'native/debug-event-clock.jsonl').splitlines()if json.loads(line)['debugEventSequence']==48784)
 assert journal['pc']==read['pc']==0x40d445 and journal['threadId']==read['threadId'] and journal['hostMonotonicNs']==read['hostMonotonicNs']
 assert raw(complete/'model/observed-source-camera.u32')==bytes.fromhex(read['worldCameraHex']) and source['words']==75 and source['wrongWords']==0
 for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']:
  assert raw(complete/'model'/name)==raw(N/'comparison-current/model'/name)
 for name in sorted(p.name for p in (complete/'model').glob('portable-live-*.json')):assert raw(complete/'model'/name)==raw(N/'comparison-current/model'/name)
 app=load(H/'gles-two-stage/report.json');old_app=load(R/'artifacts/th14/perspective-publication-nov04/gles-two-stage/report.json')
 app_build=load(H/'gles-build/build.json');assert app_build['coreBuildSha256']==SHA(raw(core_path)) and app_build['coreWasmSha256']==core['wasmSha256']
 assert SHA(raw(H/'gles-build/application.wasm'))==app_build['wasmSha256'];bind_recorded(app_build['sourceBindings'])
 for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert SHA(raw(Path(app_build['frozenApplicationSourceRoot'])/name))==digest
 assert raw(H/'gles-two-stage/run-tool.py')==raw(R/'tools/th14-native-application-process-host-oct27.py')
 assert load(H/'application-end.json')['exitCode']==0 and app['completed'] and not app['error'] and app['frames']==2289 and len(app['checks'])==27
 assert app['checks']==old_app['checks'] and all(x['passed']for x in app['checks']) and app['captures']==old_app['captures']
 assert app['pcmFrames']==1526784 and app['pcmSha256']==old_app['pcmSha256'] and app['physicalAudioDevicesOpened']==0
 for capture in app['captures']:
  for name in [capture['file'],capture['liveAnimations']['file']]:assert raw(H/'gles-two-stage'/name)==raw(R/'artifacts/th14/perspective-publication-nov04/gles-two-stage'/name)
 browser=load(H/'browser/build.json');assert browser['compiled'] and browser['compiledUnits']==146 and browser['wasmSha256']=='87fe1da1d30b38b4390e98080b885aaaa31496cad93cee677eaac0015bb705b1'
 assert browser['reusedObjectCount']==0 and not browser['browserAcceptance'] and not browser['retailAssetsIncluded']
 assert SHA(raw(H/'browser/th14-sdl.wasm'))==browser['wasmSha256'] and SHA(raw(H/'browser/th14-sdl.mjs'))==browser['loaderSha256']
 assert browser['toolSha256']==SHA(raw(R/'tools/th14-build-frozen-render-dimensions-browser-nov04.py'))
 for name,binding in browser['sourceBindings'].items():
  data=raw(H/'browser/source'/name);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
 syntax=load(H/'render-dimensions-syntax/report.json');assert syntax['passed'] and len(syntax['cases'])==16
 old=load(H/'old-rng-comparison/model/report.json');old_camera=load(H/'old-rng-comparison/model/camera-report.json');assert old['differenceCounts']=={'21':4137,'22':283,'26':1} and old['firstDifference']['index']==30837 and old_camera['counts']=={'12':16701}
 assert not load(H/'old-rng-comparison/end.json')['strictAndIndependentPassed']
 legacy=load(R/'artifacts/th14/mode-perspective-window-diagnostic-nov04/verified.json');assert legacy['verifiedLegacyModeWindowDiagnostics'] and legacy['wrongExpandedWords']==0 and legacy['diagnosticRecords']==12
 assert legacy['verifierSha256']==SHA(raw(R/'tools/th14-mode-perspective-window-evidence-nov04.py')) and legacy['strictSceneContractRejectsDriver'] and not legacy['legacyDefaultFailuresClosed']
 bind_recorded(legacy['bindings'])
 return dict(verifiedCameraRenderDimensions=True,productionIntegrated=True,changedProductionFiles=4,ordinaryCoreWasmSha256=core['wasmSha256'],cameraBytes=300,nativeDimensionIndices=[22,23],nativeResetProfiles=8,nativeResetWords=64,
  mappedPrefixWords=75,nativePrefixCases=76,componentComparedWords=5700,componentWrongWords=0,componentFailureCases=9,referenceReadWords=456,
  all141CoreObjectsFresh=True,metadataRecoveryRecompiledObjects=0,initialStageSizeAssertionFailurePreserved=True,sourceLineEndingOnlyNormalizations=len(normalizations),
  legacyStrictRecords=16,legacyStrictCallbacks=1379760,rejectedOriginalRecords=1,rejectedOriginalExceptions=12,
  expandedCameraFields=73,mixedClockRecords=16,mixedClockDiagnosticRecords=12,mixedClockComparedWords=total_words,mixedClockWrongWords=0,cases=cases,
  witnessedCallbacks=35000,witnessedCameraWords=34999*73,witnessedSourceWords=75,witnessedSourceWrongWords=0,
  applicationFrames=2289,applicationChecks=27,applicationImages=2,applicationOfflinePcmFrames=1526784,applicationAgainstFrozenReferenceOnly=True,
  browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],sharedSyntaxCases=16,physicalAudioDevicesOpenedByModel=0,
  hostClockWindowReplaysExplicit=True,strictSceneWhitelistNotBroadened=True,oldRngDifferences=[4137,283,1],oldCameraDifferences=16701,oldFailureClosed=False,
  noUnmappedNativeCameraWordsInComponent=True,wholeRunUncapturedCameraWords=[73,74],screenMatrixMathSkippedInDimensionDataflowReference=True,
  independentSchedulingAccepted=False,browserAcceptance=False,originalWholeRunPixelsOrPcmAccepted=False,completeGame=False,nativeEquivalent=False,
  protectedFiles=integration['protectedFiles'],bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting')
 result=verify()
 if a.check:assert json.loads(out.read_bytes())==result
 else:
  assert not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
 print(json.dumps({key:value for key,value in result.items()if key not in('bindings','protectedFiles','cases')}))


if __name__=='__main__':main()
