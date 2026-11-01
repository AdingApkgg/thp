"""Link the multiple-observed-clock fixture using verified existing game objects."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]
S=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base_path=a.base.resolve(strict=True);out=a.output.resolve()
    assert base_path.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    base=json.loads(base_path.read_bytes());assert len(base['objectBindings'])==141 and base['productionNormalVmReturnPoll']
    for row in base['objectBindings']:assert S(Path(row['path']))==row['sha256']
    for name in ['GameBattle.cpp','GameSession.cpp','AnmManager.cpp']:
        key='th12_web/cpp/game/'+name;assert S(R/'runtimes/th12'/key)==base['sourceHashes'][key]
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert S(compiler)==base['compilerSha256']
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-passive-vm-clocks-fixture-nov01.cpp';out.mkdir(parents=True)
    env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    command=[str(compiler),*base['flags'],*base['linkFlags'],str(fixture),*[r['path']for r in base['objectBindings']],'-o',str(out/'observer.wasm')]
    result=subprocess.run(command,env=env,capture_output=True);(out/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    report={**base,'wasmSha256':S(out/'observer.wasm'),'fixtureGraphRoot':fixture.relative_to(R).as_posix(),
        'engineSourcesRecompiledForThisLink':0,'engineObjectsReusedForThisLink':141,'fixtureSha256':S(fixture),'baseBuildSha256':S(base_path),
        'buildToolSha256':S(Path(__file__)),'testOnlyMultipleObservedHostClocks':True,'maximumClockObservations':8,
        'vmCallbackPointersWrapped':False,'nativeRngCounterInputOrPointerValuesProvided':False,'rootProductionGameplayModified':False,
        'unusedHistoricalGraphicsHeaderInventoryNotPartOfAcceptance':True,'completeGame':False,'nativeEquivalent':False}
    (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(fixtureCompiled=True,engineObjectsReused=141,engineObjectsRecompiled=0,wasmSha256=report['wasmSha256'])))
if __name__=='__main__':main()
