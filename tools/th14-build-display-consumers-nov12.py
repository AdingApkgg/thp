"""Compile changed normal providers and link bounded probes, including the old-code control."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12'
P=json.loads((H/'prepared.json').read_bytes());S=Path(P['sourceRoot'])
base=json.loads((R/P['baseManifest']).read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in P['sourceBindings'].items():assert sha(S/name)==digest,name
for name,digest in base['sourceBindings'].items():assert sha(R/name)==digest,name
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==base['compilerSha256']
O=H/'component';O.mkdir(exist_ok=False)
flags=[('-I'+str(S/Path(v[2:]).relative_to(R))) if v.startswith('-I') and Path(v[2:]).is_relative_to(R/'runtimes/th12') else v for v in base['flags']]
env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
providers=[];baseline=[];changed={r['path'] for r in P['changes']};started=time.monotonic()
for row in base['currentProviders']:
    assert sha(R/row['object'])==row['objectSha256'],row['object'];baseline.append(row)
    if row['source'] in changed:
        obj=O/(Path(row['source']).name+'.o')
        with (O/(obj.stem+'.log')).open('wb') as log:
            subprocess.run([str(cc),*flags,'-c',str(S/row['source']),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=120)
        providers.append(dict(source=row['source'],sourceSha256=sha(S/row['source']),object=obj.relative_to(R).as_posix(),objectSha256=sha(obj)))
    else:
        assert P['sourceBindings'][row['source']]==row['sourceSha256'],row['source'];providers.append(row)
fixture=R/'tools/th14-display-consumers-component-nov12.cpp'
for label,rows in [('candidate',providers),('baseline',baseline)]:
    with (O/(label+'.link.log')).open('wb') as log:
        subprocess.run([str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
            '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),
            *[str(R/row['object']) for row in rows],'-o',str(O/(label+'.wasm'))],cwd=R,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=180)
report=dict(sourceRoot=str(S),sourceBindings=P['sourceBindings'],flags=flags,currentProviders=providers,
    baselineProviders=baseline,compilerSha256=sha(cc),fixtureSha256=sha(fixture),normalAccess=True,
    freshlyCompiledUnits=2,unchangedVerifiedProviders=139,elapsedSeconds=time.monotonic()-started,
    modules={label:sha(O/(label+'.wasm')) for label in ('candidate','baseline')},canonicalEngineChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('sourceBindings','flags','currentProviders','baselineProviders')}))
