"""Relink a read-only fixture over all 141 unchanged, hash-bound engine objects."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda data:hashlib.sha256(data).hexdigest()
BASE=R/'artifacts/th14/supervisor-pass-rng-nov05/resource-clock-build-retry1/observer-build.json'

def main(out):
 assert not out.exists();out.mkdir(parents=True);base_raw=BASE.read_bytes();base=json.loads(base_raw)
 assert base['wasmSha256']=='e526651326714596a0751dcfb43faa4fa8fb0ee79e39fff4917c5b2d8339318a'
 for row in base['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
 for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():assert SHA((Path(base['sourceSnapshotRoot'])/name).read_bytes())==digest
 for name,digest in base['fixtureDependencyHashes'].items():assert SHA(Path(name).read_bytes())==digest,name
 fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-shot-lifetime-observer-nov05.cpp';text=fixture.read_text()
 old='#include "th14-supervisor-resource-clock-fixture-nov05.cpp"';assert text.count(old)==1
 text=text.replace(old,'#include "'+Path(base['fixtureGraphRoot']).as_posix()+'"')
 frozen=out/'fixture.cpp';frozen.write_text(text,encoding='utf8',newline='\n')
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==base['compilerSha256']
 argv=[str(compiler),*base['flags'],*base['linkFlags'],str(frozen),*[row['path']for row in base['objectBindings']],'-o',str(out/'observer.wasm')]
 (out/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
 env={**os.environ,'TEMP':str(out),'TMP':str(out)}
 with(out/'link.log').open('wb')as log:process=subprocess.run(argv,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 assert process.returncode==0,(out/'link.log').read_text()[-4000:]
 dependencies=dict(base['fixtureDependencyHashes']);dependencies[frozen.as_posix()]=SHA(frozen.read_bytes())
 report=dict(base);report.update(fixtureGraphRoot=str(frozen),expandedFixtureSha256=SHA(frozen.read_bytes()),fixtureDependencyHashes=dependencies,
  wasmSha256=SHA((out/'observer.wasm').read_bytes()),baseBuildSha256=SHA(base_raw),readOnlyShotLifetimeObserverAdded=True,
  engineSourcesRecompiledForThisLink=0,engineObjectsReusedForThisLink=141,rootProductionSourcesModified=False,
  observerSourceSha256=SHA(fixture.read_bytes()),buildToolSha256=SHA(Path(__file__).read_bytes()),ordinaryIndependentTimingAccepted=False,completeGame=False)
 (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(compiled=True,engineObjectsReused=141,wasmSha256=report['wasmSha256'],completeGame=False)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14');main(out)
