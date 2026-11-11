"""Link both actual mode8 render paths with controlled graphics, no physical GPU."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-display-space-nov12'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
core=load(R/'artifacts/th14/control-main-stop-nov12/current-core/build.json')
candidate=load(H/'candidate-v2/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
for row in core['currentProviders']:assert sha(Path(row['object']))==row['objectSha256']
fixture=R/'tools/th14-mode8-display-renderer-component-nov12.cpp'
for mode in ['baseline','candidate']:
 out=H/(mode+'-draw');assert not out.exists();out.mkdir()
 flags=core['flags'] if mode=='baseline' else candidate['flags']+['-DTH14_MODE8_SPACE_CANDIDATE=1']
 objects=[x['object'] for x in core['currentProviders']] if mode=='baseline' else candidate['objects']
 cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
  '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(out/'probe.wasm')]
 with (out/'build.log').open('wb') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
 (out/'fixture-source-used.cpp').write_bytes(fixture.read_bytes())
 report=dict(mode=mode,wasmSha256=sha(out/'probe.wasm'),fixtureSha256=sha(fixture),includedFixtureSha256=sha(R/'tools/th14-mode8-display-component-nov12.cpp'),
  compilerSha256=sha(cc),flags=flags,objects={str(Path(p).relative_to(R)).replace('\\','/'):sha(Path(p)) for p in objects},
  normalProviderAccess=True,actualAnmRendererDraw=True,actualMode8Branch=True,graphicsRecordingBoundaryOnly=True,
  noGpuOrAudio=True,productionChanged=False,completeGame=False,command=cmd)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(mode=mode,compiled=True,wasmSha256=report['wasmSha256'])))
