"""Compile a private current-provider quad caller candidate before adoption."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';baseline=(H/'baseline-source/AnmRenderer.cpp').read_text();assert source.read_text()==baseline
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
for row in core['currentProviders']:assert sha(Path(row['object']))==row['objectSha256']
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];fixture=R/'tools/th14-quad-display-renderer-component-nov12.cpp'
space='const float display_scale=float(render_width)/640.f;const AnmRenderSpace space{display_scale,{float(i32(render_width)/2),float((i32(render_height)-448)/2)},{float(i32(render_width)/2),float(i32(float(display_scale*16.f)))}};'
needle='Vec3 positions[4];if(!anm_quad_positions(vm,positions))return -2;';assert baseline.count(needle)==1
candidate=baseline.replace(needle,'#if PORT_TITLE == 14\n    '+space+'\n    Vec3 positions[4];if(!anm_quad_positions(vm,positions,space))return -2;\n#else\n    '+needle+'\n#endif')
needle='Vec3 positions[4];if(!anm_th14_draw_quad_positions(vm,positions))return -2;';assert candidate.count(needle)==1
candidate=candidate.replace(needle,space+'\n        Vec3 positions[4];if(!anm_th14_draw_quad_positions(vm,positions,space))return -2;')
cs=H/'candidate-source';assert not cs.exists();cs.mkdir();(cs/'AnmRenderer.cpp').write_text(candidate,encoding='utf8')
vfs=H/'candidate-vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(cs/'AnmRenderer.cpp')}]}))
for mode in ['baseline','candidate']:
 out=H/mode;assert not out.exists();out.mkdir();flags=core['flags']+(['-ivfsoverlay',str(vfs)]if mode=='candidate'else[]);objects=[]
 for row in core['currentProviders']:
  if mode=='candidate'and Path(row['source']).name=='AnmRenderer.cpp':
   obj=out/'AnmRenderer.cpp.o';cmd=[str(cc),*flags,'-c',str(source),'-o',str(obj)]
   with(out/'compile.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
   objects.append(str(obj))
  else:objects.append(row['object'])
 cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(out/'probe.wasm')]
 with(out/'build.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
 report=dict(mode=mode,wasmSha256=sha(out/'probe.wasm'),fixtureSha256=sha(fixture),includedFixtureSha256=sha(R/'tools/th14-mode8-display-component-nov12.cpp'),rendererSha256=sha(source if mode=='baseline'else cs/'AnmRenderer.cpp'),compilerSha256=sha(cc),objects={str(Path(p).relative_to(R)).replace('\\','/'):sha(Path(p))for p in objects},normalProviderAccess=True,actualRenderer=True,recordingGraphicsOnly=True,newGameRuns=0,audibleOutput=False,completeGame=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(mode=mode,compiled=True,wasmSha256=report['wasmSha256'])),flush=True)
