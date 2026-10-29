"""Compile one read-only Application adapter; reuse all verified production objects."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
base=args.base.resolve();out=args.output.resolve();assert base.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
report=json.loads((base/'build.json').read_bytes());assert report['compiled']and report['backend']=='gles'and len(report['coreObjects'])==141
for name,row in report['sourceBindings'].items():assert SHA((ROOT/name).read_bytes())==row['sha256'],name
for row in report['coreObjects']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
reused=[]
for name,digest in report['newObjects'].items():
 if name=='fixture.o':continue
 p=base/name;assert SHA(p.read_bytes())==digest;reused.append(p)
assert len(reused)==4
out.mkdir();fixture=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-native-application-player-fixture.cpp'
compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==report['compilerSha256']
flags=report['flags'];obj=out/'fixture.o';env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
build=subprocess.run([str(compiler),*flags,'-c',str(fixture),'-o',str(obj)],cwd=ROOT,env=env,capture_output=True);(out/'fixture.compile.log').write_bytes(build.stdout+build.stderr);assert build.returncode==0,build.stderr.decode()[-4000:]
exports=report['exports']+['component_player_observations'];link=report['linkFlags']+['-Wl,--export=component_player_observations'];objects=[obj,*reused,*[Path(row['path'])for row in report['coreObjects']]]
result=subprocess.run([str(compiler),*flags,*map(str,objects),*link,'-o',str(out/'application.wasm')],cwd=ROOT,env=env,capture_output=True);(out/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode()[-4000:]
bindings={name:row for name,row in report['sourceBindings'].items()if name!=str((base/'fixture.cpp').relative_to(ROOT)).replace('\\','/')}
bindings[fixture.relative_to(ROOT).as_posix()]={'bytes':fixture.stat().st_size,'sha256':SHA(fixture.read_bytes())}
report.update(toolSha256=SHA(Path(__file__).read_bytes()),sourceBindings=bindings,exports=exports,linkFlags=link,wasmSha256=SHA((out/'application.wasm').read_bytes()),newObjects={obj.name:SHA(obj.read_bytes()),**{p.name:SHA(p.read_bytes())for p in reused}},baseBuildSha256=SHA((base/'build.json').read_bytes()),reusedDeviceObjects=[{'path':p.relative_to(ROOT).as_posix(),'sha256':SHA(p.read_bytes())}for p in reused],readOnlyBeforePlayerObserver=True,observerRowsBound=32768,observerWordsPerRow=34,productionSourcesChanged=False)
(out/'gl-signatures.json').write_bytes((base/'gl-signatures.json').read_bytes());(out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'compiledAdapterObjects':1,'verifiedReusedCoreObjects':141,'verifiedReusedDeviceObjects':4,'wasmSha256':report['wasmSha256'],'boundedReadOnlyRows':32768}))
