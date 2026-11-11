"""Qualify the exact TH14 pixel-coordinate broadcast with display wiring."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';candidate=(H/'candidate-source/AnmRenderer.cpp').read_text();old='if(pixel)for(auto& p:positions){p.x=float(std::nearbyint(double(p.x))-.5);p.y=float(std::nearbyint(double(p.y))-.5);}'
new='''if(pixel){
#if PORT_TITLE == 14
        // Retail4757b4..475816 rounds four coordinates, then broadcasts.
        const float left=float(std::nearbyint(double(positions[0].x))-.5),right=float(std::nearbyint(double(positions[1].x))-.5);
        const float top=float(std::nearbyint(double(positions[0].y))-.5),bottom=float(std::nearbyint(double(positions[2].y))-.5);
        for(u32 i=0;i<4;++i){positions[i].x=(i&1)?right:left;positions[i].y=(i&2)?bottom:top;}
#else
        for(auto& p:positions){p.x=float(std::nearbyint(double(p.x))-.5);p.y=float(std::nearbyint(double(p.y))-.5);}
#endif
    }'''
assert candidate.count(old)==1;candidate=candidate.replace(old,new);cs=H/'candidate-source-v3';assert not cs.exists();cs.mkdir();(cs/'AnmRenderer.cpp').write_text(candidate,encoding='utf8')
vfs=H/'candidate-vfs-v3.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(cs/'AnmRenderer.cpp')}]}))
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';flags=core['flags']+['-ivfsoverlay',str(vfs)];assert sha(cc)==core['compilerSha256'];out=H/'candidate-v3';assert not out.exists();out.mkdir();objects=[]
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
for row in core['currentProviders']:
 assert sha(Path(row['object']))==row['objectSha256']
 if Path(row['source']).name=='AnmRenderer.cpp':
  obj=out/'AnmRenderer.cpp.o'
  with(out/'compile.log').open('wb')as f:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
  objects.append(str(obj))
 else:objects.append(row['object'])
fixture=R/'tools/th14-quad-display-renderer-component-nov12.cpp';cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(out/'probe.wasm')]
with(out/'build.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
report=dict(mode='candidate',wasmSha256=sha(out/'probe.wasm'),fixtureSha256=sha(fixture),includedFixtureSha256=sha(R/'tools/th14-mode8-display-component-nov12.cpp'),rendererSha256=sha(cs/'AnmRenderer.cpp'),objects={Path(p).relative_to(R).as_posix():sha(Path(p))for p in objects},normalProviderAccess=True,actualRenderer=True,recordingGraphicsOnly=True,newGameRuns=0,audibleOutput=False,completeGame=False)
(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');alias=H/'rotations/candidate-v3';assert not alias.exists();alias.mkdir();os.link(out/'probe.wasm',alias/'probe.wasm');(alias/'build.json').write_bytes((out/'build.json').read_bytes());print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'])))
