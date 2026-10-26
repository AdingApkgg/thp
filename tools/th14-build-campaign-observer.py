"""Link the portable TH14 campaign observer against a hash-bound core build."""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-build',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allow-unrelated-resourcecrypt-edit',action='store_true')
    parser.add_argument('--allow-unused-renderer-header-edit',action='store_true',
        help='Exclude a changed SDL Renderer.hpp only when absent from every reused core source and fixture include graph')
    args=parser.parse_args();base=json.loads(args.reuse_build.read_text())
    out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14');out.mkdir(exist_ok=False)
    crypt='th12_web/cpp/game/ResourceCrypt.cpp';excluded=[];unused_header='portable/sdl/Renderer.hpp';unused_header_candidate=False
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        actual=SHA((ROOT/'runtimes/th12'/name).read_bytes())
        if actual!=digest and name==crypt and args.allow_unrelated_resourcecrypt_edit:excluded.append(name)
        elif actual!=digest and name==unused_header and args.allow_unused_renderer_header_edit:unused_header_candidate=True
        else:assert actual==digest,name
    objects=[]
    for row in base['objectBindings']:
        p=Path(row['path']);assert SHA(p.read_bytes())==row['sha256'],str(p);objects.append(str(p))
    fixture=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-native-campaign-fixture.cpp'
    dependencies={}
    include_dirs=[ROOT/'runtimes/th12/th12_web/cpp/game',ROOT/'runtimes/th12/th12_web/cpp/sdl']
    def scan(p):
        p=p.resolve();key=p.as_posix()
        if key in dependencies:return
        raw=p.read_bytes();dependencies[key]=SHA(raw)
        cache=ROOT/'artifacts/th14/shared-observer-source-cache';cache.mkdir(exist_ok=True)
        retained=cache/(dependencies[key]+'.bin')
        if not retained.exists():retained.write_bytes(raw)
        assert SHA(retained.read_bytes())==dependencies[key];retained.chmod(stat.S_IREAD)
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode(),re.M):
            candidates=[p.parent/name,*[d/name for d in include_dirs]]
            child=next((v for v in candidates if v.exists()),None);assert child,name;scan(child)
    scan(fixture)
    fixture_dependencies=dict(dependencies)
    unused_header_proof=None
    if unused_header_candidate:
        # The old build inventories all portable headers, including unused SDL
        # ones. Do not relax a core ABI check: walk every actual source first.
        for name in base['sourceHashes']:scan(ROOT/'runtimes/th12'/name)
        changed=(ROOT/'runtimes/th12'/unused_header).resolve().as_posix()
        assert changed not in dependencies,'Changed Renderer header is an actual core/fixture dependency'
        excluded.append(unused_header)
        unused_header_proof=dict(path=unused_header,absentFromAllCoreAndFixtureIncludeGraphs=True,
            scannedCoreSources=len(base['sourceHashes']),includeGraphFiles=len(dependencies),
            currentSha256=SHA(Path(changed).read_bytes()),reusedHeaderSha256=base['headerHashes'][unused_header])
    compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576']
    wasm=out/'observer.wasm'
    result=subprocess.run([str(compiler),*flags,*['-I'+str(d)for d in include_dirs],str(fixture),*objects,'-o',str(wasm)],env=dict(os.environ,TEMP=str(out),TMP=str(out)),capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (out/'link.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
    report={**base,'wasmSha256':SHA(wasm.read_bytes()),'fixtureGraphRoot':fixture.as_posix(),'expandedFixtureSha256':SHA(fixture.read_bytes()),'fixtureDependencyHashes':fixture_dependencies,'fixtureDependenciesPortableWithinRepository':True,'engineSourcesRecompiledForThisLink':0,'engineObjectsReusedForThisLink':len(objects),'unrelatedWorkingTreeSourceEditsExcluded':excluded,'unusedRendererHeaderProof':unused_header_proof,'reuseBuildSha256':SHA(args.reuse_build.read_bytes()),'buildToolSha256':SHA(Path(__file__).read_bytes()),'completeGame':False,'nativeEquivalent':False}
    (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(wasmSha256=report['wasmSha256'],engineObjectsReused=len(objects),fixtureDependencies=len(fixture_dependencies))),flush=True)

if __name__=='__main__':main()
