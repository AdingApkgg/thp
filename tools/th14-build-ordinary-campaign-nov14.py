"""Build the ordinary held-input fixture using a verified current Application build.

Only the fixture is recompiled. Its decoder supplies physical held masks and
never restores replay globals, RNG, position, stock or completion into play.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--base',type=Path,default=R/'artifacts/th14/ordinary-loadouts-nov13/canonical-component')
 parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args();base=args.base.resolve();out=args.out.resolve()
 assert out.is_relative_to(R/'artifacts/th14');out.mkdir(parents=True,exist_ok=False)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=json.loads((base/'build.json').read_bytes())
 for name,digest in {**j['sourceBindingsByMode']['candidate'],**j['objectBindings']}.items():assert sha(R/name)==digest,name
 fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-ordinary-campaign-flow-fixture.cpp'
 source=fixture.read_text();assert 'finish_live_boundary'not in source and 'fixture_physical_held()'in source
 command=json.loads((base/'command.json').read_bytes());command=[str(fixture)if x==str(R/'runtimes/th12/th12_web/tests/cpp/th14-ordinary-loadout-flow-fixture.cpp')else str(out/'candidate.wasm')if x==str(base/'candidate.wasm')else x for x in command]
 assert str(fixture)in command and command[-1]==str(out/'candidate.wasm')
 (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
 with(out/'build.log').open('wb')as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TEMP=str(out),TMP=str(out)))
 assert result.returncode==0,(out/'build.log').read_text(errors='replace')[-3000:]
 bindings={name:digest for name,digest in j['sourceBindingsByMode']['candidate'].items()if not name.startswith(base.relative_to(R).as_posix()+'/') and not name.endswith('/th14-ordinary-loadout-flow-fixture.cpp')}
 for p in [fixture,fixture.with_name('Th14WarmAttractCase.hpp')]:bindings[p.relative_to(R).as_posix()]=sha(p)
 for name,digest in bindings.items():assert sha(R/name)==digest,name
 j.update(sourceBindingsByMode={'candidate':bindings},fixtureSha256=sha(fixture),outputs={'candidate':{'wasmSha256':sha(out/'candidate.wasm')}},ordinaryHeldInputOnly=True,completionMethodsNotExposed=True,productionGameCodeChanged=False,sourceFixture=fixture.relative_to(R).as_posix(),builderSha256=sha(Path(__file__)))
 (out/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({'compiled':True,'providerObjectsVerified':len(j['objectBindings']),'wasmSha256':sha(out/'candidate.wasm')}))
if __name__=='__main__':main()
