from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';P=json.loads((H/'prepared.json').read_bytes());S=Path(P['sourceRoot']);O=H/'candidate';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();base=json.loads((R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json').read_bytes())
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==base['compilerSha256']
for path,d in P['sourceBindings'].items():assert sha(S/path)==d,path
flags=[('-I'+str(S/Path(v[2:]).relative_to(R))) if v.startswith('-I') and Path(v[2:]).is_relative_to(R/'runtimes/th12') else v for v in base['flags']]
objects=[];began=time.monotonic();env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
for row in base['currentProviders']:
    source=S/row['source'];out=O/(source.name+'.o')
    with (O/(source.name+'.log')).open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(out)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env=env)
    objects.append(dict(source=row['source'],sourceSha256=sha(source),object=out.relative_to(R).as_posix(),objectSha256=sha(out)))
assert len(objects)==141
report=dict(sourceRoot=str(S),sourceBindings=P['sourceBindings'],flags=flags,objects=objects,compilerSha256=sha(cc),freshlyCompiledGameUnits=141,normalAccess=True,elapsedSeconds=time.monotonic()-began,rootProductionSourcesChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','flags','objects']}))
