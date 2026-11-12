from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';fixture=R/'tools/th14-camera-right-pair-component-nov12.cpp'
for mode in ['baseline','candidate']:
    O=H/(mode+'-component');O.mkdir(exist_ok=False)
    if mode=='baseline':
        b=json.loads((R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json').read_bytes());objects={r['object']:r['objectSha256'] for r in b['currentProviders']};source_root=R
    else:
        b=json.loads((H/'candidate/build.json').read_bytes());objects={r['object']:r['objectSha256'] for r in b['objects']};source_root=Path(b['sourceRoot'])
    for p,d in b['sourceBindings'].items():assert sha(source_root/p)==d,p
    for p,d in objects.items():assert sha(Path(p) if Path(p).is_absolute() else R/p)==d,p
    cmd=[str(cc),*b['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=16777216','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(Path(p) if Path(p).is_absolute() else R/p) for p in objects],'-o',str(O/'probe.wasm')]
    with (O/'link.log').open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
    out=dict(mode=mode,sourceRoot=str(source_root),sourceBindings=b['sourceBindings'],objectBindings=objects,fixtureSha256=sha(fixture),wasmSha256=sha(O/'probe.wasm'),normalAccess=True,completeGame=False)
    (O/'build.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(mode=mode,wasmSha256=out['wasmSha256'])))
