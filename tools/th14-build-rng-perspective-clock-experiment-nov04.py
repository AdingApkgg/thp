"""Link an explicitly controlled Stage clock experiment to the unchanged published core."""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--core-build',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.mkdir(parents=True)
    base_path=a.core_build.resolve(strict=True);assert base_path.is_relative_to(R/'artifacts/th14')
    base_bytes=base_path.read_bytes();base=json.loads(base_bytes)
    assert sha((base_path.parent/'observer.wasm').read_bytes())==base['wasmSha256']
    for row in base['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
    assert len(base['objectBindings'])==141
    source=Path(base['sourceSnapshotRoot']);include=[source/'th12_web/cpp'/part for part in ('game','sdl')]
    include.append(R/'runtimes/th12/th12_web/tests/cpp')
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():assert sha((source/name).read_bytes())==digest
    fixture=include[-1]/'th14-rng-perspective-clock-experiment-fixture-nov04.cpp'
    assert (include[-1]/'th14-initialization-clock-fixture-nov01.cpp').read_bytes()==Path(base['fixtureGraphRoot']).read_bytes()
    frozen=out/'fixture-source.cpp';frozen.write_bytes(fixture.read_bytes());dependencies={}
    def scan(path):
        path=path.resolve();key=path.as_posix()
        if key in dependencies:return
        raw=path.read_bytes();dependencies[key]=sha(raw)
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode(),re.M):
            child=next((q for q in [path.parent/name,*[directory/name for directory in include]]if q.exists()),None)
            assert child,name;scan(child)
    scan(frozen)
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(compiler.read_bytes())==base['compilerSha256']
    flags=[flag for flag in base['flags']if not flag.startswith('-I')]+['-I'+str(directory)for directory in include]
    env={**os.environ,'TEMP':str(out),'TMP':str(out)}
    command=[str(compiler),*flags,*base['linkFlags'],str(frozen),*[row['path']for row in base['objectBindings']],'-o',str(out/'observer.wasm')]
    (out/'compile-argv.json').write_bytes((json.dumps(command,indent=2)+'\n').encode())
    result=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180)
    (out/'compile.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-2500:]
    for name,digest in dependencies.items():assert sha(Path(name).read_bytes())==digest
    report=dict(compiled=True,readOnlyObserver=True,sourceHashes=base['sourceHashes'],headerHashes=base['headerHashes'],
        objectBindings=base['objectBindings'],flags=flags,linkFlags=base['linkFlags'],sourceSnapshotRoot=base['sourceSnapshotRoot'],
        fixtureGraphRoot=str(frozen),expandedFixtureSha256=sha(frozen.read_bytes()),fixtureDependencyHashes=dependencies,
        fixtureConservativeHeaderInventory=True,fixtureExtraIncludeDirectory=str(include[-1]),
        wasmSha256=sha((out/'observer.wasm').read_bytes()),compilerSha256=base['compilerSha256'],buildToolSha256=sha(Path(__file__).read_bytes()),
        baseBuildSha256=sha(base_bytes),engineSourcesRecompiledForThisLink=0,engineObjectsReusedForThisLink=141,
        nativeValuesProvidedToEngine=False,hostClockOverridesAdded=True,controlledTimingExperimentOnly=True,originalScheduleRecovered=False,rootProductionSourcesModified=False,
        completeGame=False,nativeEquivalent=False)
    (out/'observer-build.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps({key:report[key]for key in ('compiled','wasmSha256','engineObjectsReusedForThisLink')}))


if __name__=='__main__':main()
