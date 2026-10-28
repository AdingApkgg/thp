"""Recompile native core objects from an immutable browser source snapshot."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--browser-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();home=a.browser_build.resolve(strict=True);out=a.output.resolve()
    assert home.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('snapshot_core_storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out,100*1024**3,128*1024**2)
    build_raw=(home/'build.json').read_bytes();build=json.loads(build_raw);assert build['compiled']and build['rootUnrelatedResourceCryptExcluded'];source=home/'source'
    sources={};headers={}
    for name,row in build['sourceBindings'].items():
        raw=(source/name).read_bytes();assert SHA(raw)==row['sha256']
        if name.startswith('th12_web/cpp/game/')and name.endswith('.cpp'):sources[name]=row['sha256']
        elif Path(name).suffix in ('.h','.hpp','.inc'):headers[name]=row['sha256']
    assert len(sources)==141 and sources['th12_web/cpp/game/ResourceCrypt.cpp']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',*['-I'+str(source/n)for n in ('th12_web/cpp/game','th12_web/cpp/sdl')]]
    objects=out/'objects';objects.mkdir();env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    def compile_unit(name):
        target=objects/(Path(name).name+'.o');result=subprocess.run([str(compiler),*flags,'-c',str(source/name),'-o',str(target)],env=env,capture_output=True);(objects/(Path(name).name+'.log')).write_bytes(result.stdout+result.stderr);assert result.returncode==0,(name,result.stderr.decode(errors='replace')[-3000:]);return dict(path=target.as_posix(),sha256=SHA(target.read_bytes()))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for index,row in enumerate(pool.map(compile_unit,sorted(sources)),1):
            rows.append(row)
            if index%16==0:print('compiled',index,'/',len(sources),flush=True)
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-native-campaign-fixture.cpp';fixture_raw=fixture.read_bytes();(out/'fixture.cpp').write_bytes(fixture_raw)
    linkflags=['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576'];wasm=out/'observer.wasm';result=subprocess.run([str(compiler),*flags,*linkflags,str(out/'fixture.cpp'),*[row['path']for row in rows],'-o',str(wasm)],env=env,capture_output=True);(out/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
    storage.check_budget(out,100*1024**3,128*1024**2)
    report=dict(compiled=True,readOnlyObserver=True,sourceHashes=sources,headerHashes=headers,objectBindings=rows,flags=flags,linkFlags=linkflags,wasmSha256=SHA(wasm.read_bytes()),fixtureGraphRoot=fixture.as_posix(),expandedFixtureSha256=SHA(fixture_raw),engineSourcesRecompiledForThisLink=141,engineObjectsReusedForThisLink=0,compilerSha256=SHA(compiler.read_bytes()),buildToolSha256=SHA(Path(__file__).read_bytes()),browserBuildSha256=SHA(build_raw),immutableSourceSnapshot=source.relative_to(R).as_posix(),unrelatedRootResourceCryptExcluded=True,completeGame=False,nativeEquivalent=False)
    (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiledNativeCoreUnits=141,rootResourceCryptExcluded=True,wasmSha256=report['wasmSha256'],completeGame=False)),flush=True)
if __name__=='__main__':main()
