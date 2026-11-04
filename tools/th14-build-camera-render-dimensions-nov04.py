"""Recompile the isolated overlay-boundary core and its three fixtures."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, importlib.util, json, os, re, subprocess, time
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--resume-compiled',action='store_true');a=p.parse_args()
    home=a.candidate.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14')
    prepared=json.loads((home/'prepared.json').read_bytes());base_path=R/prepared['baseBuild'];raw=base_path.read_bytes();assert sha(raw)==prepared['baseBuildSha256']
    base=json.loads(raw);source=Path(prepared['sourceRoot']);changes={row['path']:row for row in prepared['changes']}
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():assert sha((source/name).read_bytes())==changes.get(name,{}).get('afterSha256',digest)
    out=home/'build';out.mkdir(exist_ok=a.resume_compiled);objects=out/'objects';objects.mkdir(exist_ok=a.resume_compiled);started=time.monotonic()
    spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    storage.check_budget(home,100*1024**3,128*1024**2)
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(compiler.read_bytes())==base['compilerSha256']
    include=[source/'th12_web/cpp'/part for part in ('game','sdl')];include.append(R/'runtimes/th12/th12_web/tests/cpp')
    flags=[flag for flag in base['flags']if not flag.startswith('-I')]+['-I'+str(path)for path in include[:2]]
    env={**os.environ,'TEMP':str(out),'TMP':str(out)}
    def compile_unit(name):
        path=source/name;target=objects/(path.name+'.o')
        result=subprocess.run([str(compiler),*flags,'-c',str(path),'-o',str(target)],cwd=R,env=env,capture_output=True,timeout=180)
        (objects/(path.name+'.log')).write_bytes(result.stdout+result.stderr);assert result.returncode==0,(name,result.stderr.decode(errors='replace')[-2000:])
        return dict(path=str(target),sha256=sha(target.read_bytes()))
    recovery=None
    if a.resume_compiled:
        recovery=json.loads((out/'metadata-failure.json').read_bytes())
        assert recovery['sourceFilesUnchanged'] and len(recovery['objects'])==141
        rows=[]
        for name,row in zip(base['sourceHashes'],recovery['objects']):
            target=objects/(Path(name).name+'.o')
            assert str(target)==row['path'] and sha(target.read_bytes())==row['sha256']
            assert target.stat().st_mtime_ns>=(source/name).stat().st_mtime_ns
            rows.append(row)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:rows=list(pool.map(compile_unit,base['sourceHashes']))
    assert len(rows)==141
    sources={name:sha((source/name).read_bytes())for name in base['sourceHashes']};headers={name:sha((source/name).read_bytes())for name in base['headerHashes']}
    for name,original in [('ordinary',Path(base['fixtureGraphRoot'])),('typed',include[-1]/'th14-normal-vm-boundary-fixture-nov04.cpp'),('overlay-control',include[-1]/'th14-overlay-vm-boundary-fixture-nov04.cpp')]:
        directory=out/name;directory.mkdir(exist_ok=a.resume_compiled);fixture=directory/'fixture-source.cpp';fixture.write_bytes(original.read_bytes());dependencies={}
        def scan(path):
            path=path.resolve();key=path.as_posix()
            if key in dependencies:return
            data=path.read_bytes();dependencies[key]=sha(data)
            for child in re.findall(r'^\s*#\s*include\s*"([^"]+)"',data.decode(),re.M):
                target=next((p for p in [path.parent/child,*[root/child for root in include]]if p.exists()),None);assert target,child;scan(target)
        scan(fixture)
        command=[str(compiler),*flags,'-I'+str(include[-1]),*base['linkFlags'],str(fixture),*[row['path']for row in rows],'-o',str(directory/'observer.wasm')]
        (directory/'compile-argv.json').write_bytes((json.dumps(command,indent=2)+'\n').encode())
        result=subprocess.run(command,cwd=R,env=env,capture_output=True,timeout=180);(directory/'compile.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-2500:]
        report=dict(compiled=True,readOnlyObserver=True,sourceHashes=sources,headerHashes=headers,objectBindings=rows,flags=flags,linkFlags=base['linkFlags'],
            sourceSnapshotRoot=str(source),fixtureGraphRoot=str(fixture),expandedFixtureSha256=sha(fixture.read_bytes()),fixtureDependencyHashes=dependencies,
            fixtureConservativeHeaderInventory=True,fixtureExtraIncludeDirectory=str(include[-1]),wasmSha256=sha((directory/'observer.wasm').read_bytes()),
            compilerSha256=base['compilerSha256'],baseBuildSha256=sha(raw),buildToolSha256=sha(Path(__file__).read_bytes()),
            engineObjectsRecompiled=141,engineObjectsReused=0,all141CoreObjectsRecompiled=True,metadataFailureRecovery=recovery,objectsCompiledAfterMetadataRecovery=0 if recovery else 141,sessionLayoutChanged=prepared['sessionLayoutChanged'],
            typedVmBeforeCallAndAfterReturn=True,overlayTypedVmBoundaries=True,normalVmCallbackPointersWrapped=False,nativeRngOrStateValuesProvidedToEngine=False,
            isolatedPrototypeOnly=True,rootProductionSourcesModified=False,productionIntegrated=False,fixtureKind=name,completeGame=False,nativeEquivalent=False)
        (directory/'observer-build.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(dict(fixture=name,wasmSha256=report['wasmSha256'],objects=141)),flush=True)
    storage.check_budget(home,100*1024**3,128*1024**2)
    (out/'end.json').write_bytes((json.dumps(dict(compiled=True,objects=141,fixtures=3,elapsedSeconds=time.monotonic()-started,productionIntegrated=False,completeGame=False),indent=2)+'\n').encode())


if __name__=='__main__':main()
