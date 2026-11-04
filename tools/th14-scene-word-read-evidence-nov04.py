"""Qualify the integrated Scene read job, whole warm replay and its counterexample."""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/scene-camera-read-job-nov04';J=R/'artifacts/th14/camera-normalize-store-order-nov04';N=R/'artifacts/th14/full-camera-replay-cursor-nov04/full-run/native';SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify(require_modes=True,require_application=True):
 bindings={}
 def raw(path):
  path=Path(path);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 def bind(records):
  for name,item in records.items():
   data=raw(R/name);assert len(data)==item['bytes']and SHA(data)==item['sha256'],name
 def module(name):
  path=R/'tools'/name;raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 assert sys.byteorder=='little'
 prep=load(H/'prepared.json');integration=load(H/'integration.json');assert integration['productionIntegrated']and len(prep['changes'])==3
 for item in prep['changes']:
  assert SHA(raw(Path(prep['sourceRoot'])/item['path']))==item['afterSha256']==SHA(raw(R/'runtimes/th12'/item['path']))
  if item['beforeSha256']:assert SHA(raw(H/'before-integration'/Path(item['path']).name))==item['beforeSha256']
 assert raw(R/'runtimes/th12/th12_web/cpp/game/SceneCamera.cpp')==raw(J/'source/th12_web/cpp/game/SceneCamera.cpp')
 assert prep['sourcePreparationToolSha256']==SHA(raw(R/'tools/th14-prepare-scene-camera-read-job-nov04.py'))
 ordinary_path=H/'session-build/ordinary/observer-build.json';ordinary=load(ordinary_path);assert ordinary['all141CoreObjectsRecompiled']and ordinary['engineObjectsRecompiled']==141 and ordinary['engineObjectsReused']==0
 assert ordinary['wasmSha256']=='b4bd0c7cf675e97c978cb87373785134efbfba301c78bbd8982fd2d92581004a'==SHA(raw(ordinary_path.parent/'observer.wasm'))
 assert ordinary['buildToolSha256']==SHA(raw(R/'tools/th14-build-scene-camera-read-job-nov04.py'))
 for item in ordinary['objectBindings']:assert SHA(raw(item['path']))==item['sha256']
 for name,digest in {**ordinary['sourceHashes'],**ordinary['headerHashes']}.items():assert SHA(raw(Path(ordinary['sourceSnapshotRoot'])/name))==digest
 assert prep['newHeader']in ordinary['headerHashes']
 component=load(H/'observed-prefix-component-verified.json');native_component=load(H/'native-observed-prefix.json')
 assert component['verifiedResumableCameraReadJob']and component['actualReaderPrefixObserved']==16 and component['syntheticNativeRepSchedules']==72 and component['comparedWords']==5475 and component['wrongWords']==0
 assert component['nativeSha256']==SHA(raw(H/'native-observed-prefix.json'))and component['checkerSha256']==SHA(raw(R/'tools/th14-scene-camera-read-job-observed-prefix-check-nov04.mjs'))
 assert native_component['toolSha256']==SHA(raw(R/'tools/th14-scene-camera-read-job-observed-prefix-native-nov04.py'))
 isolated=load(H/'build/build.json');assert component['buildSha256']==SHA(raw(H/'build/build.json'))and component['wasmSha256']==isolated['wasmSha256']==SHA(raw(H/'build/component.wasm'))
 for name,digest in isolated['dependencyHashes'].items():assert SHA(raw(name))==digest
 normalize=load(J/'component-verified.json');assert normalize['verifiedNormalizeStoreBoundaries']and normalize['oldPointsCannotRepresentActualSourceRead']and not normalize['actualReadDifferences']and not normalize['actualCopiedDifferences']
 assert normalize['checkerSha256']==SHA(raw(R/'tools/th14-camera-normalize-stores-check-nov04.mjs'))
 native=load(N/'report.json');count=native['callbacks'];assert count==122285 and not native['error']and not native['debugErrors']and native['recordedStages']==[1,2,3,4,5,6]
 assert native['observedForcedReplayEndMenu']and native['instructionBytesPatched']==0 and native['rngOrCounterWrites']==0 and native['caseInitialization']['attractBitClearOnly']
 assert native['configuredMusicAndSoundVolumeZero']and native['debuggerPausesAffectTiming']and not native['ordinaryMenuReplayInitialization']
 assert SHA(raw(N/'observer-source.py'))==native['sourceSha256']and native_component['nativeReportSha256']==SHA(raw(N/'report.json'))
 assert not native['actualDeclaredInputExhaustionBranchObserved']and not native['actualAllFfffMarkerBranchObserved']
 camera=raw(N/'world-camera.raw');tail=raw(N/'world-camera-tail.u32');cursor=raw(N/'replay-cursor.u32');selected=raw(N/'selected-state.u32')
 assert len(camera)==count*292 and len(tail)==count*8 and len(cursor)==count*56 and len(selected)==count*128
 for data,key in [(camera,'worldCameraSha256'),(tail,'worldCameraTailSha256'),(cursor,'replayCursorSha256'),(selected,'selectedSha256')]:assert SHA(data)==native[key]
 combined=b''.join(camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]for i in range(count))
 rows=list(struct.iter_unpack('<14I',cursor));corpus=R/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs';metadata=load(corpus/'reimub-normal-source.json');decoded=raw(corpus/'reimub-normal-decoded.bin')
 assert metadata['actualNativeCodecVerified']and metadata['decodedSha256']==SHA(decoded)and metadata['sha256']==native['sourceFullReplaySha256']==SHA(raw(corpus/'reimub-normal.rpy'))
 headers={};offset=0x94
 for stage in range(1,7):
  number,seed,frames,payload=struct.unpack_from('<HHII',decoded,offset);assert number==stage and payload>=frames*6;headers[stage]=(seed,frames,payload,offset+0xdc);offset+=0xdc+payload
 assert offset==len(decoded);previous=None;terminal_counts=collections.Counter();exhausted_stages=set()
 for row in rows:
  status,manager,mode,stage,header,pointer,fps,current,callback,declared,packed,payload,low,high=row
  assert mode==1 and stage in headers and current==callback and current<0x80000000
  seed,frames,wanted_payload,start=headers[stage];assert(declared,packed,payload)==(frames,(seed<<16)|stage,wanted_payload)
  consumed=min(current,frames);assert pointer==header+0xdc+consumed*6 and fps==header+0xdc+frames*6+(consumed+29)//30
  assert status==(31 if current<frames else 15)
  if current<frames:assert struct.pack('<2I',low,high)[:6]==decoded[start+current*6:start+(current+1)*6]
  else:assert low==high==0
  if previous:
   assert (stage==previous[3]and current==previous[7]+1)or(stage==previous[3]+1 and current==1)
  else:assert stage==1 and current==1
  if current>frames:exhausted_stages.add(stage)
  previous=row;terminal_counts[stage]=current
 assert exhausted_stages=={1,2,3,4,5}and rows[-1][7:10]==(26089,26089,26469)
 assert sum(terminal_counts.values())==count and sum(headers[s][1]for s in headers)==122385
 projection=b''.join(struct.pack('<4I',row[3],row[7],row[8],row[9])for row in rows[1:])
 builder=module('th14-prepare-scene-word-read-driver-nov04.py');driver=R/'tools'/builder.NAME;assert raw(driver)==builder.source();driver_sha=SHA(raw(driver))
 for name in ['th14-prepare-source-camera-rng-driver-nov04.py','th14-prepare-source-read-camera-cursor-driver-nov04.py','th14-prepare-camera-cursor-driver-nov04.py','th14-prepare-75-camera-driver-nov04.py']:raw(R/'tools'/name)
 observer_path=H/'session-observer-v2/observer-build.json';observer=load(observer_path);wasm=SHA(raw(observer_path.parent/'observer.wasm'));assert wasm==observer['wasmSha256']=='22f5abbc63eb71509088ccc822064894d3bc472c3dac89f5a73372e540cf4d0d'
 assert observer['objectBindings']==ordinary['objectBindings']and observer['baseBuildSha256']==SHA(raw(ordinary_path))
 for name,digest in observer['fixtureDependencyHashes'].items():assert SHA(raw(name))==digest
 positive=H/'full-observed-comparison-v4/model';negative=H/'full-without-reader-pause/model';pr=load(positive/'report.json');nr=load(negative/'report.json')
 for home,report in [(positive,pr),(negative,nr)]:
  assert report['wasmSha256']==wasm and report['comparisonToolSha256']==driver_sha and report['callbacks']==count and not report['diagnosticPrefixOnly']and not report['differenceCounts']
  assert report['noRngSerialCounterHealthOrInputWrites']and report['noPerFrameStateOverrides']and not report['ordinaryIndependentThreadTimingAcceptance']
  assert raw(home/'selected-state.u32')==selected and raw(home/'replay-cursor.u32')==projection
  assert not load(home/'replay-cursor-report.json')['counts']
 full=load(positive/'full-camera-report.json');assert full['nativeWordIndices']==list(range(75))and full['callbacksCompared']==count-1 and not full['counts']and raw(positive/'full-camera.u32')==combined[300:]
 assert full['nativeAll75CameraSha256']==SHA(combined)and full['nativeTailSha256']==SHA(tail)
 bad=load(negative/'full-camera-report.json');expected_fields=[24,25,26,28,29,30,32,33,34,36,37,38,40,45,50,54];assert bad['counts']=={str(i):20906 for i in expected_fields}
 av=memoryview(raw(negative/'full-camera.u32')).cast('I');ev=memoryview(combined[300:]).cast('I')
 observed={str(i):sum(a!=b for a,b in zip(av[i::75],ev[i::75]))for i in range(75)if av[i::75]!=ev[i::75]};assert observed==bad['counts']
 payloads=['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']+[p.name for p in sorted(positive.glob('portable-live-*.json'))]+[p.name for p in sorted(positive.glob('portable-allocations-*.json'))]
 for name in payloads:assert raw(positive/name)==raw(negative/name)
 source=load(positive/'source-read-camera-report.json');assert len(source['snapshots'])==4 and all(not s['differences']for s in source['snapshots'])
 read_job=load(positive/'scene-word-read-report.json');assert read_job['partialSceneCopyMode']==1 and len(read_job['partialSceneSnapshots'])==len(read_job['auxiliaryReadSnapshots'])==1
 job=read_job['partialSceneSnapshots'][0];assert job['state']==[75191,13,16,75,1,1,1,62,62,1,0,4]and not job['differences']and job['window']['readerPausePrefixObserved']and job['window']['publisherStart13AndResumeScheduleInferred']
 auxiliary=read_job['auxiliaryReadSnapshots'][0];assert auxiliary['state']==[51599,10,6,14,1]and not auxiliary['differences']
 negative_job=load(negative/'scene-word-read-report.json')['partialSceneSnapshots'][0];assert negative_job['state']==[75191,13,16,75,1,1,1,0,0,1,0,4]and negative_job['differences']==expected_fields
 assert pr['firstScriptReadPoint']==0 and len(pr['firstScriptReadWindows'])==1 and pr['firstScriptReadWindows'][0]['completedScriptCallsAfterRestore']==22 and not pr['firstScriptReadWindows'][0]['originalVmIdentityIsInput']
 gate=load(H/'raw-verified.json');bind(gate['bindings']);assert gate['verifiedFiniteEvidence']and gate['callbacks']==count and gate['vm303Rows']==2411 and gate['combatCheckpoints']==1044 and gate['nonemptyCombatCheckpoints']==159
 assert gate['wasmSha256']==wasm and gate['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-campaign.py'))
 rejection=load(H/'strict-scene-rejection.json');assert rejection['expectedRejection']and not rejection['whitelistChanged']and rejection['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-scene-boundaries-nov03.py'))and rejection['logSha256']==SHA(raw(H/'strict-scene-rejection.log'))
 strict_count=strict_callbacks=0
 if require_modes:
  modes=load(H/'remaining-modes-end.json');assert modes['currentStrictPasses']==16 and modes['wasmSha256']==ordinary['wasmSha256']
  for case in modes['cases']:
   if case.get('notRunOnCurrentCore'):assert case['key']=='reimub-easy'and case['exceptions']==12;continue
   record=load(H/'regressions'/case['key']/'raw-verified.json');assert record['verifiedFiniteEvidence']and record['wasmSha256']==ordinary['wasmSha256'];bind(record['bindings']);strict_count+=1;strict_callbacks+=record['callbacks']
  assert strict_count==16 and strict_callbacks==1379760
 application={}
 if require_application:
  app=load(H/'gles-two-stage/report.json');reference=load(J/'gles-two-stage/report.json');assert app['completed']and not app['error']and app['frames']==2289 and len(app['checks'])==27 and all(x['passed']for x in app['checks'])
  assert app['pcmFrames']==reference['pcmFrames']==1526784 and app['pcmSha256']==reference['pcmSha256']and app['physicalAudioDevicesOpened']==0
  for capture in app['captures']:
   for name in [capture['file'],capture['liveAnimations']['file']]:assert raw(H/'gles-two-stage'/name)==raw(J/'gles-two-stage'/name)
  application=dict(frames=2289,checks=27,images=2,offlinePcmFrames=1526784,physicalAudioDevicesOpened=0,referenceIsPreviousApplication=True)
 browser=load(H/'browser/build.json');assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and browser['reusedObjectCount']==0 and not browser['browserAcceptance']
 for name,digest in {**ordinary['sourceHashes'],**ordinary['headerHashes']}.items():assert browser['sourceBindings'][name]['sha256']==digest
 for name,item in browser['sourceBindings'].items():
  data=raw(H/'browser/source'/name);assert SHA(data)==item['sha256']and len(data)==item['bytes']
 assert browser['wasmSha256']==SHA(raw(H/'browser/th14-sdl.wasm'))
 syntax=load(H/'shared-syntax/verified.json');assert syntax['passed']and syntax['ordinaryWasmSha256']==ordinary['wasmSha256']and len(syntax['cases'])==8 and all(row['exitCode']==0 for row in syntax['cases'])
 retained_negative=load(H/'old-rng-comparison/model/report.json');assert retained_negative['wasmSha256']==ordinary['wasmSha256']and retained_negative['differenceCounts']=={'21':4137,'22':283,'26':1}
 for name,digest in integration['protectedFiles'].items():assert SHA(raw(R/name))==digest
 return dict(verifiedIntegratedSceneWordReadJob=True,productionIntegrated=True,changedGameSourceFiles=4,all141CoreObjectsFresh=True,ordinaryWasmSha256=ordinary['wasmSha256'],observationWasmSha256=wasm,
  nativeCallbacks=count,nativeStages=[1,2,3,4,5,6],originalDebugExceptions=0,nativeNaturalForcedEndMenuObserved=True,expandedCameraCallbacks=count-1,cameraFields=75,cameraComparedWords=(count-1)*75,cameraWrongWords=0,
  replayCursorFields=4,replayCursorRowsMatchNative=count-1,nativeCursorRowsMatchDecodedRules=count,inferredExhaustedIntermediateStages=sorted(exhausted_stages),actualFinalInputEofObserved=False,finalStage6InputCursor=26089,finalStage6DeclaredInputFrames=26469,finalStage6UnconsumedInputFrames=380,
  vm303Rows=2411,combatCheckpoints=1044,nonemptyCombatCheckpoints=159,originalSourceCameraSnapshots=5,completedMixedSceneCopySnapshots=1,
  observedReaderPrefix=16,inferredPublisherPrefix=13,privateOwnerWaitPolls=62,syntheticRepSchedules=72,componentWords=5475,
  sameBinaryWithoutReadPauseWrongCameraFields=16,sameBinaryWithoutReadPauseWrongCameraWords=334496,nonCameraControlPayloadsUnchanged=len(payloads),strictRetainedRecords=strict_count,strictRetainedCallbacks=strict_callbacks,
  application=application,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],sharedSyntaxCases=8,currentOrdinaryOldRngNegativeRetained=True,browserUiAccepted=False,hostClockBoundaryReplayRequired=True,partialPublicationScheduleInferred=True,exactOriginalInstructionScheduleRecovered=False,
  strictSceneWhitelistUnchanged=True,strictSceneGateAccepted=False,independentSchedulingAccepted=False,nativeStateValuesProvidedToGameSession=False,completeGame=False,nativeEquivalent=False,
  bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();result=verify();out=a.output.resolve();assert out.is_relative_to(R);encoded=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
 if a.check:assert out.read_bytes()==encoded
 else:assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(encoded)
 print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
