"""Relink both qualified caller object sets for nonzero-rotation controls."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';O=H/'rotations';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];fixture=R/'tools/th14-quad-display-renderer-component-nov12.cpp'
for mode in ['baseline','candidate']:
 parent=load(H/mode/'build.json');objects=[]
 for path,digest in parent['objects'].items():assert sha(R/path)==digest;objects.append(str(R/path))
 out=O/mode;assert not out.exists();out.mkdir();flags=core['flags'];cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(out/'probe.wasm')]
 with(out/'build.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
 report=dict(mode=mode,wasmSha256=sha(out/'probe.wasm'),fixtureSha256=sha(fixture),includedFixtureSha256=sha(R/'tools/th14-mode8-display-component-nov12.cpp'),objects=parent['objects'],rendererSha256=parent['rendererSha256'],normalProviderAccess=True,nonzeroRotations=True,actualRenderer=True,recordingGraphicsOnly=True,newGameRuns=0,audibleOutput=False,completeGame=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(mode=mode,compiled=True)),flush=True)
