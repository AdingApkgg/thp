"""Compile the one changed camera unit, reusing140 ABI-identical core objects."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 prepared_path=a.prepared.resolve();prep=json.loads(prepared_path.read_bytes());source=Path(prep['sourceRoot']);base_path=Path(prep['baseBuild']);base_bytes=base_path.read_bytes();base=json.loads(base_bytes)
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
 assert len(prep['changedFiles'])==1 and prep['changedFiles'][0]['path']=='th12_web/cpp/game/SceneCamera.cpp'
 changed=prep['changedFiles'][0];source_hashes={}
 for name,digest in base['sourceHashes'].items():
  actual=SHA((source/name).read_bytes());assert actual==(changed['afterSha256']if name==changed['path']else digest);source_hashes[name]=actual
 assert base['sourceHashes'][changed['path']]==changed['beforeSha256']
 for name,digest in base['headerHashes'].items():assert SHA((source/name).read_bytes())==digest
 objects=[dict(row)for row in base['objectBindings']];assert len(objects)==141
 for row in objects:assert SHA(Path(row['path']).read_bytes())==row['sha256']
 selected=[row for row in objects if Path(row['path']).name=='SceneCamera.cpp.o'];assert len(selected)==1
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==base['compilerSha256']
 includes=[source/'th12_web/cpp/game',source/'th12_web/cpp/sdl',R/'runtimes/th12/th12_web/tests/cpp'];flags=[flag for flag in base['flags']if not flag.startswith('-I')]+['-I'+str(path)for path in includes]
 env={**os.environ,'TEMP':str(out),'TMP':str(out)};commands=[]
 def run(argv,label):
  commands.append(argv);result=subprocess.run(argv,cwd=R,env=env,capture_output=True,timeout=180);(out/(label+'.log')).write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-2000:]
 obj=out/'SceneCamera.cpp.o';run([str(compiler),*flags,'-c',str(source/changed['path']),'-o',str(obj)],'compile-camera')
 selected[0].update(path=str(obj),sha256=SHA(obj.read_bytes()))
 frozen=out/'fixture-source.cpp';frozen.write_bytes(Path(base['fixtureGraphRoot']).read_bytes());dependencies={}
 def scan(path):
  path=path.resolve();key=path.as_posix()
  if key in dependencies:return
  data=path.read_bytes();dependencies[key]=SHA(data)
  for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',data.decode(),re.M):
   child=next((x for x in [path.parent/name,*[directory/name for directory in includes]]if x.exists()),None);assert child,name;scan(child)
 scan(frozen)
 run([str(compiler),*flags,*base['linkFlags'],str(frozen),*[row['path']for row in objects],'-o',str(out/'observer.wasm')],'link-ordinary')
 report=dict(compiled=True,readOnlyObserver=True,sourceHashes=source_hashes,headerHashes=base['headerHashes'],objectBindings=objects,
  flags=flags,linkFlags=base['linkFlags'],sourceSnapshotRoot=str(source),fixtureGraphRoot=str(frozen),expandedFixtureSha256=SHA(frozen.read_bytes()),
  fixtureDependencyHashes=dependencies,fixtureConservativeHeaderInventory=True,fixtureExtraIncludeDirectory=str(includes[-1]),
  wasmSha256=SHA((out/'observer.wasm').read_bytes()),compilerSha256=base['compilerSha256'],buildToolSha256=SHA(Path(__file__).read_bytes()),
  baseBuildSha256=SHA(base_bytes),preparedSha256=SHA(prepared_path.read_bytes()),engineSourcesRecompiledForThisLink=1,engineObjectsReusedForThisLink=140,
  headersChanged=False,sessionLayoutChanged=False,all141CoreObjectsRecompiled=False,nativeValuesProvidedToEngine=False,rootProductionSourcesModified=False,completeGame=False,nativeEquivalent=False)
 (out/'compile-argv.json').write_bytes((json.dumps(commands,indent=2)+'\n').encode());(out/'observer-build.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps({k:report[k]for k in ['compiled','wasmSha256','engineSourcesRecompiledForThisLink','engineObjectsReusedForThisLink']}))


if __name__=='__main__':main()
