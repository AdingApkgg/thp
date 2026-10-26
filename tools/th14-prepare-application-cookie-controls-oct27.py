"""Prepare a bounded Application comparison with declared process-cookie input.

Only a frozen native unit host changes. Production code, game RNG, ticks and
demo inputs stay intact. A shared external ABI input is not a whole-game proof.
"""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

ENTROPY=r'''
# The Application constructor reads std::random_device before game callbacks.
# Declare this environment input explicitly; never patch the C++ cookie, game
# RNG or later collision state. Reject an unobserved entropy protocol.
declared_entropy=[]
linker.allow_shadowing=True
def process_entropy(caller,pointer,size):
 assert size==4,('Unexpected process entropy request',size)
 raw=struct.pack('<I',args.declared_process_cookie)
 memory(caller).write(caller,raw,pointer)
 declared_entropy.append(dict(bytes=size,value=args.declared_process_cookie,beforeGameCallbacks=not globals().get('frame_index',0)))
 assert len(declared_entropy)==1,'Unexpected second process entropy request'
 (O/'declared-process-entropy.json').write_text(json.dumps(dict(events=declared_entropy,externalEnvironmentInputDeclared=True,
  productionProcessCookieForced=False,gameRngStateSupplied=False,clockSeedUnchanged=True,completeGame=False),indent=2)+chr(10))
 return 0
entropy_imports=[i for i in module.imports if i.module=='wasi_snapshot_preview1'and i.name=='random_get']
assert len(entropy_imports)==1
for imported in entropy_imports:
 linker.define(store,imported.module,imported.name,W.Func(store,imported.type,process_entropy,access_caller=True))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scope',choices=['prefix','attract'],default='prefix')
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True)
    base_path=ROOT/'tools/th14-native-application.py';base=base_path.read_bytes();runner=base.decode()
    marker='R=Path(__file__).resolve().parents[1]';assert runner.count(marker)==1
    runner=runner.replace(marker,'R=Path('+repr(str(ROOT))+')')
    marker='args=parser.parse_args();B=args.build.resolve();O=args.output.resolve()';assert runner.count(marker)==1
    runner=runner.replace(marker,"parser.add_argument('--declared-process-cookie',type=lambda text:int(text,0),required=True)\n"+marker+
        "\nassert 0<=args.declared_process_cookie<2**32 and args.declared_process_cookie!=0xbb40e64e and args.declared_process_cookie&0xffff0000")
    marker="rows=[];result=None;checks=[];completed=False;error=''";assert runner.count(marker)==1
    runner=runner.replace(marker,ENTROPY+'\n'+marker)
    assert runner.count('storage.check_budget(O)')>=2
    runner=runner.replace('storage.check_budget(O)','storage.check_budget(O,maximum_case=128*1024**2)')
    ast.parse(runner)
    (out/'base-runner.py').write_bytes(base);(out/'runner.py').write_text(runner,encoding='utf8')
    (out/'preparer.py').write_bytes(Path(__file__).read_bytes())
    scenario_path=ROOT/'runtimes/th12/th12_web/tests/fixtures/th14-native-application-attract-cycle-oct27.json'
    scenario_raw=scenario_path.read_bytes();scenario=json.loads(scenario_raw)
    assert len(scenario['actions'])==13
    if args.scope=='prefix':scenario['actions']=scenario['actions'][:7]+[dict(frames=3200,held=0,pause=0,capture='cookie-boundary')]
    (out/'scenario.json').write_text(json.dumps(scenario,indent=2)+'\n')
    bindings={}
    for path in [base_path,scenario_path,ROOT/'runtimes/th12/th12_web/cpp/sdl/Application.cpp',
        ROOT/'runtimes/th12/th12_web/cpp/game/NativeStackTh14.hpp',ROOT/'runtimes/th12/th12_web/cpp/game/ShotCallbacksTh14.cpp',
        ROOT/'runtimes/th12/th12_web/cpp/game/ShotManager.cpp']:
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
    plan=dict(schema='th14/declared-process-input-controls/1',declaredUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        cookies=[0xbb40e64f,0x4b000000],scenarioScope=args.scope,
        expectedActualFrames=11220 if args.scope=='prefix'else 17545,
        maximumFrames=15000 if args.scope=='prefix'else 27000,maximumWallSeconds=600 if args.scope=='prefix'else 900,
        minimumFreeBytes=100*1024**3,maximumOutputBytesPerCase=128*1024**2,freeBefore=shutil.disk_usage(out).free,
        sourceBindings=bindings,preparerSha256=SHA(Path(__file__).read_bytes()),runnerSha256=SHA((out/'runner.py').read_bytes()),
        scenarioSha256=SHA((out/'scenario.json').read_bytes()),productionSourcesChanged=False,gameRngStateSupplied=False,
        inputDeliveredThroughDeclaredWasiEntropy=True,originalOrdinaryApplicationAccepted=False,browserAcceptance=False,completeGame=False)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert plan['freeBefore']>plan['minimumFreeBytes']+128*1024**2,'Retain the disk reserve before starting controls'
    print(json.dumps(dict(prepared=True,output=str(out),runnerSha256=plan['runnerSha256'],actualTestNotStarted=True)))


if __name__=='__main__':main()
