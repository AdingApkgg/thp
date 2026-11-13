"""Qualify retained alpha results, guard other titles, then adopt exact code."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/alpha-range-current-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
gpu=load(O/'gpu/report.json');build=load(O/'build.json')
assert gpu['alphaCases']==8192 and gpu['differentAlphaPixels']==gpu['differentAlphaCases']==0
assert gpu['clearCases']==0 and 'ENOENT' in gpu['exception'] and 'clears.bgra' in gpu['exception']
assert gpu['closed']and gpu['gpuContextClosed']and all(n==0 for n in gpu['gpu']['liveObjects'].values())
assert all(n==0 for n in gpu['platform'].values())
assert sha(O/'probe.wasm')==gpu['wasmSha256']==build['wasmSha256']
for n,h in {**build['sourceBindings'],**build['generatedSourceBindings']}.items():assert sha(R/n)==h,n
for row in gpu['alphaHashes']:
 p=R/('artifacts/th14/gpu-alpha-low'if row['low']else'artifacts/th14/gpu-alpha')
 assert sha(p/'native.bgra')==row['actualSha256']==row['nativeSha256']
 assert sha(p/'native.json')==row['nativeManifestSha256']
source=R/'runtimes/th12/portable/sdl/Renderer.cpp';before=source.read_text();candidate=(O/'Renderer.candidate.cpp').read_text()
old=next(x for x in before.splitlines()if x.startswith('void Renderer::uniform('))
new=next(x for x in candidate.splitlines()if x.startswith('void Renderer::uniform('))
assert new!=old and candidate.count(new)==1
candidate=candidate.replace(new,'#if defined(PORT_TITLE) && PORT_TITLE == 14\n'+new+'\n#else\n'+old+'\n#endif')
fragment=''' }else
#endif
 {const float alpha=float(p.alphaReference)/255;uniform(22,1,&alpha);}
 '''
assert candidate.count(fragment)==1
candidate=candidate.replace(fragment,''' }else
 {const float alpha=float(p.alphaReference)/255;uniform(22,1,&alpha);}
#else
 float alpha=float(p.alphaReference)/255;uniform(22,1,&alpha);
#endif
 ''')
guard=O/'Renderer.guarded-v2.cpp';assert not guard.exists();guard.write_text(candidate,encoding='utf8',newline='\n')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
S=O/'source';flags=['--target=wasm32-wasip1-threads','-pthread','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-D__EMSCRIPTEN__=1','-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include'),'-I'+str(S)]
def run(cmd,log):
 with log.open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
 assert q.returncode==0,log.read_text(errors='replace')[-2500:]
vfs=O/'guard-v2-vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(S/'Renderer.cpp'),'external-contents':str(guard)}]}))
exports=['gpu_initialize','gpu_error','gpu_alpha_case','gpu_alpha_texture','gpu_alpha_boundaries','clear_case','gpu_close','allocated','released']
run([str(cc),*flags,'-DPORT_TITLE=14','-ivfsoverlay',str(vfs),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',*['-Wl,--export='+x for x in exports],str(S/'Renderer.cpp'),str(S/'fixture.cpp'),'-o',str(O/'guarded-v2.wasm')],O/'guarded-v2-build.log')
assert sha(O/'guarded-v2.wasm')==sha(O/'probe.wasm'),'TH14 guarded module must be byte-identical; do not rerun GPU'
control=O/'other-title-control-v2';control.mkdir();rows=[]
for title in [12,13,16]:
 hashes=[]
 for mode,path in [('before',O/'Renderer.before.cpp'),('after',guard)]:
  v=control/(str(title)+'-'+mode+'.vfs.json');v.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(path)}]}))
  obj=control/(str(title)+'-'+mode+'.o');run([str(cc),*flags,'-DPORT_TITLE='+str(title),'-ivfsoverlay',str(v),'-c',str(source),'-o',str(obj)],control/(str(title)+'-'+mode+'.log'));hashes.append(sha(obj))
 assert hashes[0]==hashes[1],title
 rows.append(dict(title=title,sha256=hashes[0],byteIdentical=True))
assert source.read_bytes()==(O/'Renderer.before.cpp').read_bytes()
tmp=source.with_suffix('.cpp.tmp');tmp.write_bytes(guard.read_bytes());tmp.replace(source)
report=dict(alphaCases=8192,comparedPixels=8388608,differentPixels=0,otherTitleObjectPairs=rows,
 actualGpuDriverExitCode=1,postAlphaMissingClearReferenceFailureRetained=True,
 alphaAggregateHashesIndependentlyVerified=True,clearsNotNewlyTested=True,clearImplementationUnchanged=True,
 guardedTh14WasmByteIdentical=True,sourceIntegrated=True,sourceSha256=sha(source),
 upstreamCommit='19170e47016e10d61d5e69556989b68b5cdea8e3',deferredClearsIntegrated=False,
 fullFrameOrPhysicalRngAccepted=False,published=False,deployed=False,completeGame=False)
(O/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
