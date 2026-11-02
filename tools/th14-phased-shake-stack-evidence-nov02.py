from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/phased-shake-stack-nov02';L=H/'live';N=L/'native';bindings={}
p=argparse.ArgumentParser(description='Verify the integrated phased-shake stack producer against original process and instruction evidence.');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-phased-shake-stack-nov02.json');p.add_argument('--check',action='store_true');args=p.parse_args()
sys.path.insert(0,str(R/'tools'))
SHA=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
def load(p):return json.loads(raw(p))
end=load(L/'process-end.json');native=load(N/'report.json');quiet=load(L/'native-silence-verified.json')
assert end['observerExitCode']==1 and end['guardStop']is None and end['actualMastersZero']
assert native['childExited']and not native['error']and native['diagnosticPrefixOnly']and not native['fullReplayAccepted']
assert native['phasedShakeProbeDone']and native['phasedStackObservationOnly']and native['phasedShakeAttempts']<=8
assert all(e.get('firstChance')and e.get('callbacks')==0 and e['code']==0xe06d7363 for e in native['debugErrors'])
assert native['hardwareBreakpointsOnly']and native['instructionBytesPatched']==native['rngOrCounterWrites']==0
assert not native['inputInjected']and native['gameStateWordWrites']==1 and native['caseInitialization']['attractBitClearOnly']
assert quiet['verifiedActualNativeMasterLevelsZero']and quiet['nativePid']==native['pid']
assert len(quiet['samples'])==2 and all(all(s[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster'])for s in quiet['samples'])
source=raw(N/'observer-source.py');assert SHA(source)==native['sourceSha256']
published_observer=raw(R/'tools/th14-phased-shake-live-observer-nov02.py')
assert published_observer==source.replace(b'\r\n',b'\n').replace(b'\r',b'\n')
assert ast.dump(ast.parse(published_observer),include_attributes=False)==ast.dump(ast.parse(source),include_attributes=False)
base=raw(R/'tools/th14-native-campaign-observer-oct25.py');assert SHA(base)=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
def calls(s,name):return [ast.dump(x,include_attributes=False)for x in ast.walk(ast.parse(s))if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr==name]
for name in ['WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext','TerminateProcess']:assert calls(source,name)==calls(base,name),name
events=raw(N/'phased-shake-stack-events.jsonl');assert SHA(events)==native['phasedShakeEventsSha256']
events=[json.loads(s)for s in events.splitlines()];assert len(events)==native['phasedShakeEvents']
ret=[e for e in events if e['event']=='callback-return'and e['secondReturn']is not None];assert len(ret)==1
ret=ret[0];entry=[e for e in events if e['event']=='entry'and e['attempt']==ret['attempt']];assert len(entry)==1;entry=entry[0]
assert all(e['readOnly']and not e['providedToEngine']for e in events)
assert entry['pc']==0x46cf60 and entry['registers']['esp']==entry['callbackEntryEsp']
assert entry['observedSlot']==ret['observedSlot']==entry['callbackEntryEsp']-56
assert ret['pc']==entry['returnPc']==0x4012f7 and ret['registers']['esp']==entry['callbackEntryEsp']+4
assert ret['registers']['eax']==1
draw=ret['secondReturn'];write=ret['lastWrite']
assert draw['pc']==0x46d0c9 and draw['registers']['eax']&65535==ret['word']==write['word']==write['registers']['ebx']
assert ret['neighborWord']==0x4db510 and ret['neighborWord']!=ret['word']
assert entry['hostMonotonicNs']<write['hostMonotonicNs']<draw['hostMonotonicNs']<ret['hostMonotonicNs']
modules=load(N/'phased-live-modules.json');dlls=[e for e in modules['rows']if e['name'].lower()=='ntdll.dll'and e['base']<2**32];assert len(dlls)==1
dll=dlls[0];assert SHA(Path(dll['path']).read_bytes())=='23d7772221e7a763ccf3f3fe39592086eb3091603554c4981f0ab430fa2ca686'
assert write['pc']==dll['base']+333408+9 and write['instructionContext'].startswith('5356')
# Execute the complete native component again, binding the intact DLL and
# synthetic environment. No live pointer or RNG word becomes engine input.
tool=R/'tools/th14-phased-shake-stack-native-nov02.py';raw(tool)
spec=importlib.util.spec_from_file_location('phase_native',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
oracle=load(H/'native-v3.json');assert module.observe()==oracle and len(oracle['cases'])==2016
component=load(H/'component-verified.json');assert component['passed']and component['comparedRngActiveCases']==480
assert component['results']['baseline']['stackFailures']==192 and component['results']['candidate']['differenceWords']==0
assert component['results']['candidate']['wrongOffsetControls']==192
for kind in ['baseline','candidate']:
 folder=H/('component-'+kind);build=load(folder/'build.json');assert SHA(raw(folder/'component.wasm'))==build['wasmSha256']
 for name,digest in build['sourceHashes'].items():assert SHA(raw(folder/'source'/name))==digest
syntax=load(H/'syntax/report.json');assert syntax['passed']and len(syntax['results'])==8 and all(r['exitCode']==0 for r in syntax['results'])
base_build=load(R/'artifacts/th14/rng-store-boundary-nov02/regular-core-v2/observer-build.json');build=load(H/'full-candidate/observer-build.json')
assert SHA(raw(H/'full-candidate/observer.wasm'))==build['wasmSha256']and len(build['objectBindings'])==141
changed=[]
for group in ['sourceHashes','headerHashes']:
 assert build[group].keys()==base_build[group].keys()
 for name,digest in build[group].items():
  assert SHA(raw(Path(build['sourceSnapshotRoot'])/name))==digest
  if digest!=base_build[group][name]:changed.append(name)
assert set(changed)=={'th12_web/cpp/game/'+x for x in ['ScreenShake.hpp','ScreenShake.cpp','NativeStackTh14.hpp']}
for name in changed:
 previous=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show','4acbbc398fe3648ca8362e4fe803f56ee87818b7:runtimes/th12/'+name])
 assert SHA(previous)==base_build['sourceHashes'].get(name,base_build['headerHashes'].get(name))
 assert SHA(raw(R/'runtimes/th12'/name))==build['sourceHashes'].get(name,build['headerHashes'].get(name))
for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
assert build['fixtureGraphRoot']==base_build['fixtureGraphRoot']and build['expandedFixtureSha256']==base_build['expandedFixtureSha256']
regressions=load(H/'full-regressions/end.json');assert regressions['allCasesActuallyExecuted']and regressions['casesCompleted']==regressions['strictPasses']==regressions['independentPasses']==16 and regressions['callbacks']==1579705
for case in regressions['results']:
 assert case['strictPassed']and case['exitCode']==case['independentVerifierExitCode']==0 and case['guardStop']is case['independentGuardStop']is None
 folder=R/case['caseDirectory'];proof=load(folder/'raw-verified.json');assert proof['verifiedFiniteEvidence']and proof['wasmSha256']==build['wasmSha256']
 assert proof['allVm303AndRegistryOrderEqual']and proof['allCapturedCombatWordsEqual']and not proof['diagnosticPrefixOnly']
 for name,binding in proof['bindings'].items():assert SHA((R/name).read_bytes())==binding['sha256'],name
integration=load(H/'integration.json');production=load(H/'production-core/observer-build.json')
assert integration['productionIntegrated']and integration['candidateAndProductionWasmExactlyEqual']and integration['exportAbiIdentical']and integration['exports']==134
assert production['promotedFromExactVerifiedCandidate']and production['ordinaryFixtureAnd134ExportAbiUnchanged']
assert raw(H/'production-core/observer.wasm')==raw(H/'full-candidate/observer.wasm')
assert production['wasmSha256']==build['wasmSha256']and production['sourceHashes']==build['sourceHashes']and production['headerHashes']==build['headerHashes']and production['objectBindings']==build['objectBindings']
for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
 if name.endswith('/ResourceCrypt.cpp'):continue
 assert SHA(raw(R/'runtimes/th12'/name))==digest,name
current_component=load(H/'integrated-component/verified.json');current_build=load(H/'integrated-component/build.json')
assert current_component['passed']and current_component['cppActiveRngProfiles']==480 and current_component['differenceWords']==0 and current_component['wrongAdjacentStackOffsetControlsRejected']==192
assert SHA(raw(H/'integrated-component/component.wasm'))==current_build['wasmSha256']==component['results']['candidate']['wasmSha256']
for name,digest in current_build['sourceBindings'].items():assert SHA(raw(R/name))==digest,name
raw(R/'tools/th14-phased-shake-stack-component-check-nov02.py');raw(R/'tools/th14-phased-shake-stack-component-check-nov02.mjs');raw(R/'runtimes/th12/th12_web/tests/cpp/th14-phased-shake-stack-fixture-nov02.cpp')
assert SHA(raw(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
assert SHA(raw(R/'artifacts/th14/vm-return-worker-oct29/work-state.json'))=='2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
result=dict(verifiedFinitePhasedShakeStackCandidate=True,productionIntegrated=True,rootGameSourcesChanged=True,
 actualLiveOriginalPhasedCallObserved=True,nativeCallbacks=native['callbacks'],livePhasedCalls=1,
 originalComponentCases=2016,activeRngCppComparisons=480,baselineStackFailures=192,candidateDifferenceWords=0,
 wrongAdjacentStackOffsetControlsRejected=192,syntaxChecks=8,currentCandidateNaturalCases=16,currentCandidateNaturalCallbacks=1579705,
 candidateCoreWasmSha256=build['wasmSha256'],actualMastersZero=True,nativeDiagnosticExitCode=1,
 actualControllerReaderExecuted=False,retirementHeapAddressResolved=False,firstControllerLastWriterObserved=False,
 old36826StrictFailureClosed=False,independentSchedulingAccepted=False,browserAcceptance=False,
 coldStartupAccepted=False,startupFirstChanceNoticesRetained=len(native['debugErrors']),
 completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
result.update(verifiedIntegratedPhasedShakeStackRepair=True,changedFiles=['ScreenShake.hpp','ScreenShake.cpp','NativeStackTh14.hpp'],basePublishedCommit='e0c7b378ecc5741c9ab907ffcd6726f2f1ad6ad6',productionCoreWasmMatchesVerifiedCandidate=True,ordinary134ExportAbiUnchanged=True,currentCppComponentRecompiledAndMatched=True,sourceCoreObjectsCompiled=141,newCoreFullApplicationAccepted=False,newCoreBrowserAccepted=False,naturalModeInventory=30,allStageEntryModeInventory=27,capturedObserverSourceSha256=SHA(source),publishedObserverSourceSha256=SHA(published_observer),publishedObserverDiffersOnlyByExactLineEndingNormalization=True)
output=args.output.resolve();assert output.is_relative_to(R/'docs/porting')or output.is_relative_to(R/'artifacts/th14')
data=(json.dumps(result,indent=2)+'\n').encode()
if args.check:assert output.read_bytes()==data,'Evidence differs; keep the previous report and inspect the changed input'
else:output.write_bytes(data)
print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
