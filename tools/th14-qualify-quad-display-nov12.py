"""Audit exact draw/query submit phases, shared-title objects, then adopt."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bindings={}
def read(p):
 raw=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(raw).hexdigest();return raw
for dataset in [H,H/'rotations']:
 native=load(dataset/'native.json');assert native['cases']==6912 and native['inputs']==576
 for name,d in [('inputs.bin',native['inputSha256']),('outputs.u32',native['outputSha256'])]:assert hashlib.sha256(read(dataset/name)).hexdigest()==d
 query=load(dataset/'native-query/native.json');assert hashlib.sha256(read(dataset/'native-query/outputs.u32')).hexdigest()==query['outputSha256']
 submit=load(dataset/'native-submit-query/native.json');assert submit['actualOriginalX87PixelRounding']and submit['actualOriginalPositionCacheStores']
 for row in submit['routes']:assert hashlib.sha256(read(dataset/'native-submit-query'/row['path'])).hexdigest()==row['sha256']
 baseline=load(dataset/'baseline-submit-query/checked.json');candidate=load(dataset/'candidate-v3-submit-query/checked.json')
 for row in candidate['routes']:
  assert row['cases']==6912 and row['wordsCompared']==82944 and row['failedCases']==row['differentWords']==0
  assert row['actualOutputSha256']==row['nativeOutputSha256']==next(r['sha256']for r in submit['routes']if r['route']==row['route'])
 assert all(r['failedCases']>0 for r in baseline['routes'])
 build=load(dataset/'candidate-v3/build.json');assert sha(dataset/'candidate-v3/probe.wasm')==build['wasmSha256']==candidate['wasmSha256']
 for p,d in build['objects'].items():assert hashlib.sha256(read(R/p)).hexdigest()==d,p
 for name,key in [('th14-quad-display-renderer-component-nov12.cpp','fixtureSha256'),('th14-mode8-display-component-nov12.cpp','includedFixtureSha256')]:assert hashlib.sha256(read(R/'tools'/name)).hexdigest()==build[key]
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';candidate_source=H/'candidate-source-v3/AnmRenderer.cpp';before=sha(source);after=sha(candidate_source)
assert before==sha(H/'baseline-source/AnmRenderer.cpp')and after==load(H/'candidate-v3/build.json')['rendererSha256']
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];O=H/'other-titles';assert not O.exists();O.mkdir();rows=[]
for title in [12,13,16]:
 flags=[x.replace('-DPORT_TITLE=14','-DPORT_TITLE='+str(title))for x in core['flags']];digests={}
 for mode in ['baseline','candidate']:
  obj=O/f'th{title}-{mode}.o';cmd=[str(cc),*flags,*(['-ivfsoverlay',str(H/'candidate-vfs-v3.json')]if mode=='candidate'else[]),'-c',str(source),'-o',str(obj)]
  with(obj.with_suffix('.log')).open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
  digests[mode]=sha(obj)
 assert digests['baseline']==digests['candidate'];rows.append(dict(title=title,objectSha256=digests,byteIdentical=True))
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
read(Path(__file__));read(candidate_source)
report=dict(sourceBeforeSha256=before,sourceAfterSha256=after,declaredCasesPerRoute=13824,exactWordsPerRoute=165888,routes=['draw','ascii-query-plus-submit'],allCasesBitwiseExact=True,default640DrawBaselineAlreadyExact=True,asciiNonzeroPixelBroadcastGapAlsoFixed=True,actualOriginalGeometryEntries=['476100','4766e0','479560'],actualOriginalSubmitSlice='4756e0..47589b',realOriginalAsciiWrapperNotExecuted=True,declaredManagerOffsetZero=True,zeroAndNonzeroRotations=True,localZRotations=[0,.375,-.625],parentZRotations=[0,-.25,.75],sharedTitleObjects=rows,normalProviderAccess=True,unchangedGameProvidersReverified=140,sourceAdopted=True,classLayoutUnchanged=True,allEarlierBoundaryMismatchControlsRetained=True,linkTempPermissionFailureRetained=True,newOriginalGameProcesses=0,newApplicationRuns=0,newGpuRuns=0,audibleOutput=False,protectedResourceCryptUnchanged=True,browserRuntimeUpdated=False,loadingRngGapNotClosed=True,completeGame=False,bindings=bindings)
# Preserve old source inode when previous evidence used hardlinks.
t=source.with_suffix('.pending.cpp');t.write_bytes(candidate_source.read_bytes());os.replace(t,source);assert sha(source)==after
q=H/'qualified.json';assert not q.exists();q.write_text(json.dumps(report,indent=2)+'\n')
w=R/'artifacts/th14/option-recall-once-nov02/work-state.json';state=load(w);state['quadDisplaySpaceNov12']={k:v for k,v in report.items()if k!='bindings'};state['previousGoalTurnClass']='progress: TH14 quad/ASCII display wiring and original pixel-coordinate broadcast qualified and adopted; release pending.';t=w.with_suffix('.pending.json');t.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(t,w)
print(json.dumps({k:v for k,v in report.items()if k!='bindings'}))
