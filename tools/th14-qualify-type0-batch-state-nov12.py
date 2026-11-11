"""Adopt the original batch-state order after exact draw-time controls."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=load(H/'baseline/checked-v2.json');new=load(H/'candidate/checked-v2.json');native=load(H/'native-v2/report.json');assert old['failedCases']==135 and old['differentWords']==8208 and new['cases']==360 and new['failedCases']==new['differentWords']==0 and new['comparedWords']==161406 and new['nativeSubmittedVertices']==9558;assert not native['error']and native['actual475eb0FlushAnd475f80QueueExecuted']and native['finalCallerFlushDeclaredAndExecuted']
source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';candidate=H/'candidate-source/AnmRenderer.cpp';before=sha(source);assert before==sha(H/'baseline-source.cpp');build=load(H/'candidate/build.json');assert sha(candidate)==build['rendererSha256']and sha(H/'candidate/probe.wasm')==build['wasmSha256']==new['wasmSha256']
for p,d in build['objects'].items():assert sha(R/p)==d,p
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];O=H/'shared';assert not O.exists();O.mkdir();rows=[]
for title in [12,13,16]:
 flags=[f.replace('-DPORT_TITLE=14','-DPORT_TITLE='+str(title))for f in core['flags']];hashes={}
 for mode in ['baseline','candidate']:
  obj=O/f'th{title}-{mode}.o';cmd=[str(cc),*flags,*(['-ivfsoverlay',str(H/'candidate-vfs.json')]if mode=='candidate'else[]),'-c',str(source),'-o',str(obj)]
  with(obj.with_suffix('.log')).open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
  hashes[mode]=sha(obj)
 assert hashes['baseline']==hashes['candidate'];rows.append(dict(title=title,hashes=hashes,byteIdentical=True))
# Correct a comment-only address typo, while binding the unchanged object bytes.
original=candidate.read_text();corrected=original.replace('Native40abff/40a917','Native40ac01');assert corrected!=original;(H/'candidate/source-used-before-comment-correction.cpp').write_bytes(candidate.read_bytes());t=candidate.with_suffix('.pending.cpp');t.write_text(corrected,encoding='utf8');os.replace(t,candidate)
obj=O/'comment-corrected-th14.o';cmd=[str(cc),*core['flags'],'-ivfsoverlay',str(H/'candidate-vfs.json'),'-c',str(source),'-o',str(obj)]
with(O/'comment-correction.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
assert sha(obj)==sha(H/'candidate/AnmRenderer.cpp.o')
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45';after=sha(candidate)
t=source.with_suffix('.pending.cpp');t.write_bytes(candidate.read_bytes());os.replace(t,source);assert sha(source)==after
report=dict(sourceBeforeSha256=before,sourceAfterSha256=after,sourceAdopted=True,classLayoutUnchanged=True,cases=360,states=[0,1,2,3],beforeInterruptUpdates=[0,79,84],afterInterruptUpdates=[0,1,10,20,40],formats=[21,22],priorCachedBlendModes=[None,0,7],baselineFailedCases=135,baselineDifferentWords=8208,candidateFailedCases=0,comparedWords=161406,nativeSubmittedVertices=9558,originalQueue475f80AndFlush475eb0Executed=True,originalGraphicsDeviceServicesDeclared=True,finalCallerFlushDeclaredAndExecuted=True,verticesAndEffectiveBlendStatesCompared=True,inactiveAlphaFactorsNotCompared=True,textureDepthSamplerStatesNotAccepted=True,sharedTitleObjects=rows,commentCorrectionObjectByteIdentical=True,normalProviderAccess=True,newOriginalGameRuns=0,newApplicationRuns=0,noGpuPixels=True,audibleOutput=False,protectedResourceCryptUnchanged=True,browserRuntimeUpdated=False,loadingRngGapNotClosed=True,completeGame=False)
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
