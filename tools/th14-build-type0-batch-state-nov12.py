"""Build the current and private type0 batch-state candidates normally."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';text=source.read_text();old='if(alpha_pass){flush();p.separateAlphaBlend=false;if(draw(transition.embedded[4])==-2)return -2;flush();}';new='''if(alpha_pass){
        // Retail40ac7f disables separate alpha before material's pending flush.
        p.separateAlphaBlend=false;if(draw(transition.embedded[4])==-2)return -2;flush();
    }''';assert text.count(old)==1;text=text.replace(old,new);needle='p.sourceAlphaBlend=BlendFactor::SourceAlpha;p.destinationAlphaBlend=BlendFactor::One;p.alphaBlendEquation=BlendEquation::Add;';assert text.count(needle)==1;text=text.replace(needle,needle+'\n        blend_mode=10; // Native40abff/40a917 force the next material selection.')
cs=H/'candidate-source';assert not cs.exists();cs.mkdir();(cs/'AnmRenderer.cpp').write_text(text,encoding='utf8');(H/'baseline-source.cpp').write_bytes(source.read_bytes());vfs=H/'candidate-vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(cs/'AnmRenderer.cpp')}]}))
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');parent=load(R/'artifacts/th14/quad-display-space-nov12/candidate-v3/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];fixture=R/'tools/th14-type0-batch-state-component-nov12.cpp'
for mode in ['baseline','candidate']:
 O=H/mode;assert not O.exists();O.mkdir();flags=core['flags']+(['-ivfsoverlay',str(vfs)]if mode=='candidate'else[]);objects=[]
 for p,d in parent['objects'].items():
  assert sha(R/p)==d
  if mode=='candidate'and Path(p).name=='AnmRenderer.cpp.o':
   obj=O/'AnmRenderer.cpp.o'
   with(O/'compile.log').open('wb')as f:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
   objects.append(str(obj))
  else:objects.append(str(R/p))
 cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(O/'probe.wasm')]
 with(O/'build.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
 report=dict(mode=mode,wasmSha256=sha(O/'probe.wasm'),fixtureSha256=sha(fixture),rendererSha256=sha(cs/'AnmRenderer.cpp'if mode=='candidate'else source),objects={Path(p).relative_to(R).as_posix():sha(Path(p))for p in objects},normalProviderAccess=True,graphicsBoundaryOnly=True,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False)
 (O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(mode=mode,compiled=True)),flush=True)
