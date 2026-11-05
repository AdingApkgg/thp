"""Recompile all 141 game units from the immutable full GLES candidate for WASI."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1];B=R/'artifacts/th14/stage-restore-delivery-nov05/browser-build'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main(out):
 out=out.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
 assert shutil.disk_usage(R).free>=100*1024**3
 base_raw=(B/'build.json').read_bytes();base=json.loads(base_raw)
 assert base['wasmSha256']=='e6a36791815eda8fc943d41a0e09b0a8b40c01b1afa752f2ceee1e3f7df6cb11'
 for name,row in base['sourceBindings'].items():assert SHA((B/'source'/name).read_bytes())==row['sha256'],name
 out.mkdir(parents=True);source=out/'source';objects=out/'objects';objects.mkdir()
 for path in (B/'source').rglob('*'):
  if not path.is_file():continue
  target=source/path.relative_to(B/'source');target.parent.mkdir(parents=True,exist_ok=True);os.link(path,target)
 fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-independent-session-nov05.cpp'
 frozen=out/'fixture.cpp';frozen.write_bytes(fixture.read_bytes())
 units=sorted(name for name in base['objectHashes']if name.startswith('th12_web/cpp/game/'))
 assert len(units)==141
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 assert SHA(compiler.read_bytes())=='945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
 flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off',
  '-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
  *['-I'+str(source/name)for name in ['th12_web/cpp/game','th12_web/cpp/sdl','portable/sdl']]]
 env={**os.environ,'TEMP':str(objects),'TMP':str(objects)}
 def compile_unit(name):
  target=objects/(name.replace('/','_')+'.o')
  with(objects/(target.name+'.log')).open('wb')as log:
   result=subprocess.run([str(compiler),*flags,'-MMD','-MF',str(target)+'.d','-c',str(source/name),'-o',str(target)],
    cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
  assert result.returncode==0,f'Retain {target.name}.log';return target
 compiled={}
 (out/'build-tool.py').write_bytes(Path(__file__).read_bytes())
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  jobs={pool.submit(compile_unit,name):name for name in units}
  for job in concurrent.futures.as_completed(jobs):
   compiled[jobs[job]]=job.result();assert shutil.disk_usage(R).free>=100*1024**3
   (out/'progress.json').write_text(json.dumps(dict(phase='compile',compiled=len(compiled),total=141))+'\n')
   if len(compiled)%16==0:print('compiled',len(compiled),'/141',flush=True)
 link=['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576']
 argv=[str(compiler),*flags,*link,str(frozen),*[str(compiled[name])for name in units],'-o',str(out/'session.wasm')]
 (out/'link-argv.json').write_text(json.dumps(argv,indent=2)+'\n')
 with(out/'link.log').open('wb')as log:
  result=subprocess.run(argv,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 assert result.returncode==0,'Retain link.log'
 report=dict(schema='th14/independent-full-session-build/1',compiled=True,gameUnitsRecompiled=141,
  oldObjectsReused=0,sourceSnapshotRoot=source.relative_to(R).as_posix(),sourceBindings=base['sourceBindings'],
  objectHashes={name:SHA(compiled[name].read_bytes())for name in units},flags=flags,linkFlags=link,
  fixturePath=fixture.relative_to(R).as_posix(),fixtureSha256=SHA(frozen.read_bytes()),
  parentGlesBuildSha256=SHA(base_raw),parentGlesWasmSha256=base['wasmSha256'],
  wasmSha256=SHA((out/'session.wasm').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
  fullActualGameSession=True,directReplayEntry=True,observedNativeClockSchedulingUsed=False,
  gpuDeviceIsDeclaredRecordingDependency=True,audioDeviceOpened=False,originalAssetsCopied=False,
  nativeEquivalent=False,completeGame=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 (out/'progress.json').write_text(json.dumps(dict(phase='compiled',compiled=141,total=141))+'\n')
 print(json.dumps(dict(compiled=True,units=141,wasmSha256=report['wasmSha256'])),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
