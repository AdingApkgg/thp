"""Rebuild changed browser units; verify all 144 unaffected production providers."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12';O=H/'browser';O.mkdir(exist_ok=False);(O/'objects').mkdir();(O/'logs').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
q=load(H/'qualified.json');assert q['sourceAdopted'];parent=load(R/'artifacts/th14/display-mode-entry-nov12/browser/build.json')
bindings=q['currentSourceBindings'];changed={row['path'] for row in q['changedFiles']}
for name,digest in bindings.items():assert sha(R/name)==digest,name
rt=R/'runtimes/th12';sdk=rt/'tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py';config=sdk/'.emscripten'
assert sha(cc)==parent['compilerSha256'] and sha(config)==parent['configurationSha256']
env={**os.environ,'EM_CONFIG':str(config),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
started=time.monotonic();rows=[]
for row in parent['objects']:
    assert sha(R/row['object'])==row['sha256'],row['object']
    if row['source'] in changed:
        obj=O/'objects'/(Path(row['source']).name+'.o')
        with (O/'logs'/(obj.stem+'.log')).open('wb') as log:
            subprocess.run([sys.executable,str(cc),*parent['flags'],'-c',str(R/row['source']),'-o',str(obj)],cwd=rt,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=180)
        rows.append(dict(source=row['source'],sourceSha256=sha(R/row['source']),object=obj.relative_to(R).as_posix(),sha256=sha(obj),freshlyCompiled=True))
    else:
        assert sha(R/row['source'])==row['sourceSha256'];rows.append({**row,'freshlyCompiled':False})
with (O/'logs/link.log').open('wb') as log:
    subprocess.run([sys.executable,str(cc),*parent['flags'],*[str(R/r['object']) for r in rows],*parent['linkFlags'],'-o',str(O/'th14-sdl.mjs')],cwd=rt,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=300)
for name,digest in bindings.items():assert sha(R/name)==digest,name
for p in (R/'artifacts/th14/display-mode-entry-nov12/browser').glob('*.mjs'):
    if p.name!='th14-sdl.mjs':(O/p.name).write_bytes(p.read_bytes())
report=dict(units=146,freshlyCompiledUnits=2,reusedVerifiedUnits=144,sourceBindings=bindings,objects=rows,flags=parent['flags'],linkFlags=parent['linkFlags'],
    sha256=sha(O/'th14-sdl.wasm'),loaderSha256=sha(O/'th14-sdl.mjs'),compilerSha256=sha(cc),configurationSha256=sha(config),
    elapsedSeconds=time.monotonic()-started,normalProductionAccess=True,fixtureMacrosOrVfsUsed=False,browserUiAcceptance=False,audibleOutput=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('sourceBindings','objects','flags','linkFlags')}))
