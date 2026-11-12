"""Verify shared edits leave the other supported titles' generated code unchanged."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12'
P=json.loads((H/'prepared.json').read_bytes());S=Path(P['sourceRoot']);O=H/'legacy';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
base=json.loads((R/P['baseManifest']).read_bytes());assert sha(cc)==base['compilerSha256']
rows=[];started=time.monotonic()
for title in (12,13,16):
    for change in P['changes']:
        pair=[];name=change['path']
        for label,tree in [('baseline',R),('candidate',S)]:
            flags=['--target=wasm32-wasip1-threads','-pthread',f'-DPORT_TITLE={title}','-DTH_NATIVE_PLATFORM=1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-I'+str(tree/'runtimes/th12/th12_web/cpp/game')]
            obj=O/f'{title}-{Path(name).name}.{label}.o'
            with obj.with_suffix('.log').open('wb') as log:
                subprocess.run([str(cc),*flags,'-c',str(tree/name),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
            pair.append(dict(label=label,sourceSha256=sha(tree/name),object=obj.relative_to(R).as_posix(),objectSha256=sha(obj)))
        assert pair[0]['objectSha256']==pair[1]['objectSha256'],(title,name)
        rows.append(dict(title=title,source=name,objects=pair,byteIdentical=True))
result=dict(allByteIdentical=True,objectPairs=rows,compilerSha256=sha(cc),elapsedSeconds=time.monotonic()-started,newGameOrGpuRuns=0,completeGame=False)
(O/'checked.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(objectPairs=len(rows),allByteIdentical=True,elapsedSeconds=result['elapsedSeconds'])))
