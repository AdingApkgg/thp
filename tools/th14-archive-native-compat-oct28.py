"""Recompile changed units with native flags; require byte-identical objects."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core-build',type=Path,required=True)
    p.add_argument('--gles-build',type=Path,required=True)
    p.add_argument('--webgpu-build',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();O=a.output.resolve();assert O.is_relative_to(R/'artifacts/th14') and not O.exists();O.mkdir(parents=True)
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    core_raw=a.core_build.read_bytes();core=json.loads(core_raw);cases=[]
    row=next(row for row in core['objectBindings'] if Path(row['path']).name=='GameResources.cpp.o')
    cases.append(('resources',R/'runtimes/th12/th12_web/cpp/game/GameResources.cpp',core['flags'],Path(row['path']),row['sha256']))
    for label,home in [('gles',a.gles_build),('webgpu',a.webgpu_build)]:
        if home is None:continue
        report=json.loads((home/'build.json').read_bytes());assert report['compiled']
        cases.append((label,home/'fixture.cpp',report['flags'],home/'fixture.o',report['newObjects']['fixture.o']))
    rows=[]
    for label,source,flags,reference,expected in cases:
        assert not any('TH14_ARCHIVE_WORKER' in flag for flag in flags)
        assert SHA(reference.read_bytes())==expected
        output=O/(label+'.o');command=[str(compiler),*flags,'-c',str(source),'-o',str(output)]
        result=subprocess.run(command,capture_output=True,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
        (O/(label+'.compile.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,result.stderr.decode(errors='replace')[-3000:]
        digest=SHA(output.read_bytes())
        rows.append(dict(label=label,compiled=True,objectBytes=output.stat().st_size,sha256=digest,referenceSha256=expected,byteIdentical=digest==expected,command=command))
    sources={name:SHA((R/name).read_bytes()) for name in ['runtimes/th12/th12_web/cpp/game/GameResources.cpp',
        'runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/portable/sdl/Th14WebGpuCallbacks.hpp']}
    report=dict(passed=all(row['byteIdentical'] for row in rows),rows=rows,sourceBindings=sources,
        compilerSha256=SHA(compiler.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Native feature-disabled object compatibility only; no new runtime or whole-game acceptance.',
        completeGame=False,nativeEquivalent=False)
    (O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
if __name__=='__main__':main()
