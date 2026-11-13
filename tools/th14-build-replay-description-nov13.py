from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/ordinary-replay-menu-nov13/component';O=R/'artifacts/th14/replay-description-bridge-nov13';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((P/'build.json').read_bytes());cmd=json.loads((P/'command.json').read_bytes());cut=cmd.index(str(P/'fixture.cpp'))
for n,h in j['objectBindings'].items():assert sha(R/n)==h,n
fixture=R/'tools/th14-replay-description-nov13.cpp';wasm=O/'probe.wasm'
cmd=[x for x in cmd[:cut]if x!='-fno-access-control']+[str(fixture)]+[str(R/n)for n in j['objectBindings']]+['-o',str(wasm)]
(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
sources={n:sha(R/n)for n in ['runtimes/th12/th12_web/cpp/game/ReplayDescriptionTh14.hpp','runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/sdl-runtime/shell.mjs','tools/th14-replay-description-nov13.cpp']}
(O/'build.json').write_text(json.dumps(dict(wasmSha256=sha(wasm),sources=sources,objectBindings=j['objectBindings'],nativeReplayDecoderReused=True,normalAccessControl=True,productionBrowserBuild=False,completeGame=False),indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmSha256=sha(wasm),normalAccessControl=True)))
