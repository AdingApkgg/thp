"""Compare actual decoded stage values across both resource-loading APIs."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('core-build','output','archive','wasmtime-site'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True);tool_raw=Path(__file__).read_bytes();(out/'run-tool.py').write_bytes(tool_raw)
    spec=importlib.util.spec_from_file_location('decode_resource_storage',ROOT/'tools/th14-test-storage.py')
    storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    budget=lambda:storage.check_budget(out,100*1024**3,128*1024**2);budget()
    raw=a.core_build.read_bytes();core=json.loads(raw);assert core['compiled']and core['readOnlyObserver']
    for row in core['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
    fixture=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-initial-stage-decode-fixture.cpp'
    fixture_raw=fixture.read_bytes();(out/'fixture.cpp').write_bytes(fixture_raw)
    compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';wasm=out/'resource-compare.wasm'
    command=[str(compiler),*core['flags'],'-Wl,-z,stack-size=1048576',str(fixture),*[row['path']for row in core['objectBindings']],'-o',str(wasm)]
    compiled=subprocess.run(command,capture_output=True,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
    (out/'compile.log').write_bytes(compiled.stdout+compiled.stderr);assert compiled.returncode==0,compiled.stderr.decode(errors='replace')
    sys.path.insert(0,str(a.wasmtime_site.resolve()));import wasmtime as W
    wasi=W.WasiConfig();wasi.argv=['stage-resource-comparison','/input/'+a.archive.name]
    wasi.preopen_dir(str(a.archive.resolve().parent),'/input',fs_mutable=False)
    wasi.stdout_file=str(out/'stdout.jsonl');wasi.stderr_file=str(out/'stderr.log')
    engine=W.Engine();store=W.Store(engine);store.set_wasi(wasi);linker=W.Linker(engine);linker.define_wasi()
    instance=linker.instantiate(store,W.Module.from_file(engine,str(wasm)));started=time.monotonic()
    code=0;runtime_error=None
    try:instance.exports(store)['_start'](store)
    except W.ExitTrap as failure:code=failure.code
    except BaseException as failure:code=-1;runtime_error=repr(failure)
    assert SHA(fixture.read_bytes())==SHA(fixture_raw)
    rows=[json.loads(line)for line in (out/'stdout.jsonl').read_text().splitlines()if line.startswith('{')]
    with a.archive.open('rb')as stream:archive_sha256=hashlib.file_digest(stream,'sha256').hexdigest()
    result=dict(passed=code==0 and len(rows)==43 and rows[-1].get('passed')is True,exitCode=code,
        rows=rows,expectedCases=42,actualCases=sum('stage'in row for row in rows),runtimeError=runtime_error,
        declaredCommandStackBytes=1048576,coreBuildSha256=SHA(raw),fixtureSha256=SHA(fixture_raw),
        wasmSha256=SHA(wasm.read_bytes()),compilerSha256=SHA(compiler.read_bytes()),archiveSha256=archive_sha256,
        toolSha256=SHA(tool_raw),readOnlyArchive=True,physicalAudioDevicesOpened=0,
        actualByteAndFieldComparison=True,completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        elapsedSeconds=time.monotonic()-started)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');budget()
    print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
    assert result['passed'],(out/'stderr.log').read_text()[-2000:]


if __name__=='__main__':main()
