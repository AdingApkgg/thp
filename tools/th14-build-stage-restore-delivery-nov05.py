"""Rebuild the full accepted GLES source snapshot with explicit restore hooks.

Header/vtable changes require all 146 units to be rebuilt. Assets are not inputs.
The independent readiness feature is enabled in this candidate only.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys
R=Path(__file__).resolve().parents[1]
BASE=R/'artifacts/th14/raf-owned-swap-nov05/build'
SHA=lambda data:hashlib.sha256(data).hexdigest()
OVERLAYS=['th12_web/cpp/game/GameSession.cpp','th12_web/cpp/game/GameSessionResources.cpp',
 'th12_web/cpp/game/GameSessionResources.hpp','th12_web/cpp/game/ReplayRngRestoreTh14.hpp',
 'th12_web/cpp/sdl/Application.cpp','portable/sdl/Th14AsyncRuntime.mjs',
 'portable/sdl/Th14WebGpuRuntime.mjs','portable/sdl/Th14StageRestoreDelivery.mjs',
 'portable/sdl/Th14StageRestoreProtocol.mjs','portable/sdl/Th14StageRestoreWorker.mjs']

def main(out):
 out=out.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
 assert shutil.disk_usage(R).free>=100*1024**3
 before_raw=(BASE/'build.json').read_bytes();before=json.loads(before_raw)
 assert before['wasmSha256']=='7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325'
 assert before['backend']=='gles' and before['rafOwnsTiming']
 inventory=dict(before['sourceBindings'])
 for name,row in inventory.items():assert SHA((BASE/'source'/name).read_bytes())==row['sha256'],name
 assert inventory['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
 out.mkdir(parents=True);source=out/'source';objects=out/'objects';objects.mkdir()
 for path in (BASE/'source').rglob('*'):
  if not path.is_file():continue
  name=path.relative_to(BASE/'source').as_posix()
  if name in OVERLAYS:continue
  dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(path,dest)
 for name in OVERLAYS:
  raw=(R/'runtimes/th12'/name).read_bytes();dest=source/name
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  inventory[name]=dict(bytes=len(raw),sha256=SHA(raw),origin='explicit-stage-restore-delivery')
 sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
 flags=[*before['flags'],'-DTH14_STAGE_RESTORE_DELIVERY=1']
 env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,
  'EMCC_CORES':'2','TEMP':str(objects),'TMP':str(objects),'TMPDIR':str(objects)}
 units=sorted(before['objectHashes']);assert len(units)==146
 (out/'build-tool.py').write_bytes(Path(__file__).read_bytes())
 (out/'compile-inputs.json').write_text(json.dumps(dict(flags=flags,sourceBindings=inventory,overlays=OVERLAYS),indent=2)+'\n')
 def compile_unit(name):
  target=objects/(name.replace('/','_')+'.o')
  argv=[sys.executable,str(emcc),*flags,'-c',str(source/name),'-o',str(target)]
  with(objects/(target.name+'.log')).open('wb') as log:
   result=subprocess.run(argv,cwd=source/'th12_web',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  assert result.returncode==0,f'Retain compiler log: {target.name}.log'
  return target
 compiled={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  jobs={pool.submit(compile_unit,name):name for name in units}
  for job in concurrent.futures.as_completed(jobs):
   name=jobs[job];compiled[name]=job.result()
   assert shutil.disk_usage(R).free>=100*1024**3
   (out/'progress.json').write_text(json.dumps(dict(phase='compile',compiled=len(compiled),total=len(units)))+'\n')
   if len(compiled)%16==0:print('compiled',len(compiled),'/',len(units),flush=True)
 link=list(before['linkFlags'])
 # Frozen absolute JS-library path remains immutable and hash-bound through the
 # base snapshot; rewrite it to this candidate's identical frozen library.
 for index,value in enumerate(link):
  if index and link[index-1]=='--js-library':link[index]=str(source/'portable/sdl/Th14WebGpuLibrary.js')
 (out/'progress.json').write_text(json.dumps(dict(phase='link',compiled=len(compiled),total=len(units)))+'\n')
 argv=[sys.executable,str(emcc),*flags,*[str(compiled[name])for name in units],*link,'-o',str(out/'th14-sdl.mjs')]
 with(out/'link.log').open('wb') as log:
  result=subprocess.run(argv,cwd=source/'th12_web',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
 assert result.returncode==0,'Retain link.log'
 for filename in ['Th14AsyncRuntime.mjs','Th14StageRestoreDelivery.mjs','Th14StageRestoreProtocol.mjs','Th14StageRestoreWorker.mjs']:
  (out/filename).write_bytes((source/'portable/sdl'/filename).read_bytes())
 for filename in before.get('archiveWorkerFiles',{}):
  if (BASE/filename).is_file():os.link(BASE/filename,out/filename)
 report=dict(before);report.update(sourceBindings=inventory,compiledUnits=146,reusedObjectCount=0,
  reusedObjectHashes={},reusedObjectPaths={},objectHashes={name:SHA(compiled[name].read_bytes())for name in units},
  flags=flags,linkFlags=link,gameCoreObjectsReused=0,gameCoreObjectsRecompiled=141,
  rendererOnlyChanged=False,sourceHeaderAndVtableChangeRebuilt=True,
  stageRestoreDeliveryCandidate=True,independentDeliveryFeatureEnabled=True,
  independentRestoreModuleFiles={name:dict(bytes=(out/name).stat().st_size,sha256=SHA((out/name).read_bytes()))
   for name in ['Th14StageRestoreDelivery.mjs','Th14StageRestoreProtocol.mjs','Th14StageRestoreWorker.mjs']},
  wasmBytes=(out/'th14-sdl.wasm').stat().st_size,wasmSha256=SHA((out/'th14-sdl.wasm').read_bytes()),
  loaderSha256=SHA((out/'th14-sdl.mjs').read_bytes()),parentBuildReportSha256=SHA(before_raw),
  overlays=OVERLAYS,toolSha256=SHA(Path(__file__).read_bytes()),
  browserRun=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
  ordinaryIndependentSchedulingAccepted=False,rawAssetsCopied=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 (out/'progress.json').write_text(json.dumps(dict(phase='compiled',compiled=146,total=146))+'\n')
 print(json.dumps(dict(compiled=True,units=146,gameUnits=141,wasmSha256=report['wasmSha256'],browserAcceptance=False)),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
