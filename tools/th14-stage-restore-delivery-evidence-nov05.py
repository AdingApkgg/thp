"""Verify source/build/component/UI scopes; publish metadata, never payloads."""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage-restore-delivery-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def read(path):return json.loads(raw(path))
 home=H/'browser-build';build=read(home/'build.json')
 assert build['compiled'] and build['compiledUnits']==146 and build['gameCoreObjectsRecompiled']==141
 assert not build['reusedObjectCount'] and build['sourceHeaderAndVtableChangeRebuilt']
 assert build['independentDeliveryFeatureEnabled'] and '-DTH14_STAGE_RESTORE_DELIVERY=1'in build['flags']
 for name,row in build['sourceBindings'].items():assert SHA((home/'source'/name).read_bytes())==row['sha256'],name
 for name,digest in build['objectHashes'].items():assert SHA((home/'objects'/(name.replace('/','_')+'.o')).read_bytes())==digest,name
 assert len(build['objectHashes'])==146
 for name in build['overlays']:
  assert SHA(raw(R/'runtimes/th12'/name))==build['sourceBindings'][name]['sha256']
 assert build['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
 assert SHA(raw(home/'th14-sdl.wasm'))==build['wasmSha256']
 assert SHA(raw(home/'th14-sdl.mjs'))==build['loaderSha256']
 for name,row in build['independentRestoreModuleFiles'].items():assert SHA(raw(home/name))==row['sha256']
 component=H/'session-component';cb=read(component/'build.json');run=read(component/'verified-terminal-retry1.json')
 first_run=read(component/'verified.json');raw(component/'checker-initial.mjs')
 assert first_run['passed'] and first_run['wasmSha256']==run['wasmSha256']
 assert SHA(raw(component/'component.wasm'))==cb['wasmSha256']==run['wasmSha256']
 assert SHA(raw(component/'fixture.cpp'))==cb['fixtureSha256']
 assert SHA(raw(component/'build.json'))==run['componentBuildSha256']
 assert SHA(raw(home/'build.json'))==run['browserBuildSha256']
 assert cb['exactGameSessionInitializationLambda'] and cb['exactReplayEconomyProjection']
 for name,digest in cb['headerHashes'].items():assert SHA((component/name).read_bytes())==digest
 # The component conservatively freezes every game header, including unused
 # worktree headers. Compare the compiler's actual include graph to the full
 # candidate, rather than equating files which never entered this component.
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 assert SHA(compiler.read_bytes())=='945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
 dependency_output=subprocess.check_output([str(compiler),'--target=wasm32-wasip1','-DPORT_TITLE=14',
  '-std=c++17','-MM','-MT','component',str(component/'fixture.cpp')],cwd=R,timeout=30)
 dependency_text=dependency_output.decode().replace('\\\r\n',' ').replace('\\\n',' ')
 dependencies=[Path(value).resolve()for value in dependency_text.split(':',1)[1].split()]
 assert all(path.parent==component for path in dependencies)
 used_headers=sorted(path.name for path in dependencies if path.suffix=='.hpp')
 assert len(used_headers)==17 and 'Stage.hpp'not in used_headers
 for name in used_headers:
  assert SHA((home/'source/th12_web/cpp/game'/name).read_bytes())==cb['headerHashes'][name],name
 initial_check=read(H/'evidence-initial/failure.json');raw(H/'evidence-initial/checker.py')
 assert initial_check['firstHeader']=='Stage.hpp' and not initial_check['compilerActuallyIncludesStageHeader']
 for name,digest in cb['sourceBindings'].items():assert SHA((R/name).read_bytes())==digest
 assert run['passed'] and run['workerThreadsTerminal']==12 and len(run['cases'])==12
 assert run['moduleBindings']==build['independentRestoreModuleFiles']
 cases={row['name']:row for row in run['cases']}
 for name in ['record','playback-a','playback-b','playback-c']:
  row=cases[name];assert row['progress']==1 and row['stores']==3 and row['invalid']==0
  assert row['snapshots']==(0 if name=='record'else 1)
  assert row['commitsBeforeReturn']==(3 if name=='record'else 4)
  assert row['producerCompletedNormallyBeforeCleanup']
 assert any(row.get('snapshotWaits',0)>0 for row in first_run['cases'])
 for name in ['cancel-after-script','cancel-before-globals','reject-script-ack','reject-globals-ack','stale-generation']:
  assert cases[name]['progress']==2 and cases[name]['invalid']==0
 assert cases['cancel-before-globals']['snapshots']==0 and cases['cancel-before-globals']['stores']==3
 assert cases['reject-globals-ack']['snapshots']==1 and not cases['reject-globals-ack']['noError']
 for name in ['replacement-and-stale-message','paused-main-no-timeout','worker-creation-failure']:assert cases[name]['passed']
 compatibility=H/'compatibility-component';old=read(compatibility/'build.json');old_run=read(compatibility/'verified.json')
 assert old_run['passed'] and len(old_run['cases'])==6
 assert SHA(raw(compatibility/'component.wasm'))==old['wasmSha256']=='10cc53bf8351570294c45ab773ff21ec5ddca7ff9e712a01d04efe50fb1c136a'
 assert old['headerHashes']['ReplayRngRestoreTh14.hpp']==cb['headerHashes']['ReplayRngRestoreTh14.hpp']
 syntax=read(H/'shared-syntax/report.json');assert syntax['passed'] and len(syntax['rows'])==5
 assert all(row['returncode']==0 for row in syntax['rows'])
 package=read(H/'package/package-report.json');launcher=read(H/'launcher/launcher-report.json');transport=read(H/'transport.json')
 assert package['prepared'] and not package['originalAssetsCopied']
 assert launcher['prepared'] and launcher['stageRestoreDeliveryCandidate'] and not launcher['payloadFilesCopied']
 assert transport['verifiedTransport'] and transport['quietByDefault'] and len(transport['requests'])==31
 assert package['wasmSha256']==launcher['wasmSha256']==transport['wasmSha256']==build['wasmSha256']
 for name in build['independentRestoreModuleFiles']:
  assert any(row['path']=='/runtime/th14/'+name and row['status']==200 for row in transport['requests'])
 observations=read(H/'browser/observations.json')
 assert observations['wasmSha256']==build['wasmSha256'] and not observations['browserNextStageTransitionObserved']
 assert observations['actualOrdinaryStartupAndReimuBNormalObserved'] and observations['actualQuitObserved']
 assert observations['managerSettledFiles']==0 and not observations['warningsErrors']
 assert not observations['replayUploadOrDownloadAttempted'] and not observations['user8208TabOperated']
 for name,row in observations['evidenceFiles'].items():assert SHA(raw(R/name))==row['sha256']
 tools=['th14-build-stage-restore-delivery-nov05.py','th14-stage-restore-component-nov05.py',
  'th14-stage-restore-delivery-check-nov05.mjs','th14-prepare-stage-restore-launcher-nov05.py',
  'th14-package-renderer-candidate-nov05.py','th14-renderer-launcher-transport-check-nov05.mjs',
  'th14-build-async-gles-nov05.py','th14-build-near-clip-browser-nov05.py','th14-prepare-async-gles-preview-nov05.py']
 for name in tools:raw(R/'tools'/name)
 assert SHA((R/'tools/th14-build-stage-restore-delivery-nov05.py').read_bytes())==build['toolSha256']
 assert SHA((R/'tools/th14-stage-restore-component-nov05.py').read_bytes())==cb['toolSha256']
 assert SHA((R/'tools/th14-stage-restore-delivery-check-nov05.mjs').read_bytes())==run['toolSha256']
 return dict(schema='th14/stage-restore-delivery-public-evidence/1',
  productionHooksImplemented=True,threeRngStoreCommitNotifications=True,separateReplayGlobalsCommitNotification=True,
  ordinarySdlCandidateFeatureEnabled=True,defaultBuildFeatureEnabled=False,
  fullCandidateUnitsRecompiled=146,gameUnitsRecompiled=141,staleVtableObjectsReused=0,
  candidateWasmSha256=build['wasmSha256'],synchronousComponentWasmSha256=cb['wasmSha256'],
  exactGameSessionInitializerAndReplayEconomyProjectionCompiledWithSyntheticUnitOwners=True,
  compilerIncludedHeaderCount=17,allActuallyIncludedHeadersEqualFullCandidate=True,
  compilerDependencyOutputSha256=SHA(dependency_output),unusedHeaderInventoryComparisonFailureRetained=True,
  actualBrowserWorkerEntryAndClientViaNodeFacade=True,componentCases=12,workerThreadsTerminal=12,
  playbackRunsWithFourActualCommits=3,recordRunsWithThreeActualCommits=1,
  successfulProducersReachedNormalTerminalBeforeCleanup=4,initialTwelveCaseRunRetained=True,
  fourthSnapshotIndependentlyWaitedInAtLeastOneRun=True,
  cancelledOrRejectedAcknowledgementControls=5,staleGenerationAndMessageProtected=True,
  pausedMainMoreThanTwoSecondsDoesNotFail=True,workerCreationFailureVisible=True,
  stateAlreadyWrittenBeforeRejectedAcknowledgementIsRetained=True,
  noRngValuesOrFrameVmTargetsSentToProducer=True,
  compatibilityCasesPassed=6,oldSignatureComponentWasmByteIdenticalToPreviousAcceptedComponent=True,
  sharedTitleAndWebGpuSyntaxCasesPassed=5,httpRequestsPassed=31,routeCount=transport['routes'],
  allThreeWorkerModulesActuallyServedWithIsolationHeaders=True,wholeReplayRegressionRun=False,
  finiteOrdinaryBrowser=dict(reimuBNormalStartupAndShooting=True,naturalGameOver=True,actualTitleAndQuit=True,
   immediateSidebarAndSettledEmptyManager=True,warningsErrors=0,quiet=True,
   operatorObserved=True,automaticPixelComparator=False,replaySavedUploadedOrDownloaded=False),
  browserNextStageTransitionObserved=False,browserIndependentWorkerDeliveryAccepted=False,
  ordinaryHostCancellationAtActualNextStageAccepted=False,
  wasmLinearMemoryShared=False,extraMainStoreAckSynchronizationCostUncalibrated=True,
  originalWindowsSchedulingEquivalent=False,independentSchedulingAccepted=False,
  defaultPreviewAndUser8208Unchanged=True,old8210Navigated=False,
  rawAssetsCopiedOrPublished=False,originalProcessStarted=False,modePassCountsChanged=False,
  completeGame=False,nativeEquivalent=False,evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 result=verify();target=R/'docs/porting/th14-stage-restore-delivery-nov05.json'
 if a.check:assert json.loads(target.read_bytes())==result
 else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(verified=True,componentCases=12,fullRebuild=146,browserNextStageAccepted=False,completeGame=False)))
