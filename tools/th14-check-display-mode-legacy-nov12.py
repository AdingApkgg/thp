"""Compile unchanged-title controls for shared source edits; no game execution."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12';S=Path(json.loads((H/'prepared.json').read_bytes())['sourceRoot'])
args=argparse.ArgumentParser();args.add_argument('--title',type=int,choices=[12,13,16],required=True);title=args.parse_args().title
O=H/f'legacy-th{title}';O.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((H/'candidate/build.json').read_bytes());cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==base['compilerSha256'];rows=[];began=time.monotonic()
sources=['runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp','runtimes/th12/th12_web/cpp/sdl/GraphicsDevice.cpp','runtimes/th12/portable/sdl/Renderer.cpp']
for name in sources:
    objects=[]
    for label,tree in [('baseline',R),('candidate',S)]:
        rt=tree/'runtimes/th12'
        flags=['--target=wasm32-wasip1-threads','-pthread',f'-DPORT_TITLE={title}','-DTH_NATIVE_PLATFORM=1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
               '-I'+str(rt/'th12_web/cpp/game'),'-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
        obj=O/(Path(name).name+'.'+label+'.o')
        with obj.with_suffix('.log').open('wb') as log:
            subprocess.run([str(cc),*flags,'-c',str(tree/name),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180,
                env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
        objects.append(dict(label=label,sourceSha256=sha(tree/name),objectSha256=sha(obj),object=str(obj.relative_to(R))))
    assert objects[0]['objectSha256']==objects[1]['objectSha256'],name
    rows.append(dict(source=name,objects=objects,byteIdentical=True))
report=dict(title=title,objectPairs=rows,allByteIdentical=True,compilerSha256=sha(cc),elapsedSeconds=time.monotonic()-began,newGameOrGpuRuns=0,completeGame=False)
(O/'checked.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(title=title,pairs=len(rows),allByteIdentical=True,elapsedSeconds=report['elapsedSeconds'])))
