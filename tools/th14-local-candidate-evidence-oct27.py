"""Verify one frozen local candidate's sources, objects and transport receipts.

No browser is launched. Saved HTTP receipts describe their observation time;
their equality is not UI, game-flow, audio or browser acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--expected-code-commit',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse-build',type=Path,help='Required when validating reused objects; supplies their frozen build provenance')
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());return raw
    def load(path):return json.loads(read(path))
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    build=load(home/'browser-candidate/build.json');package=load(home/'browser-runtime/package-report.json')
    routes=load(home/'launcher-candidate/launcher-report.json');transport=load(home/'launcher-candidate/transport.json')
    served=load(home/'served-current.json');read(home/'verify-preview.py')
    assert build['compiled'] and build['sourceUnits']==146
    assert build['compiledUnits']+build['reusedObjectCount']==146
    assert build['basePublishedCommit']==served['basePublishedCommit']==args.expected_code_commit
    assert build['rootUnrelatedResourceCryptExcluded'] and not build['retailAssetsIncluded']
    assert build['actualSdlPort'] and build['asyncify'] and build['frameAndWorkerCallbacksSerialized']
    assert sha(read(home/'browser-candidate/build-tool.py'))==build['toolSha256']
    for path,row in build['sourceBindings'].items():
        assert sha(read(home/'browser-candidate/source'/path))==row['sha256'],path
    for path,digest in build['objectHashes'].items():
        assert sha(read(home/'browser-candidate/objects'/(path.replace('/','_')+'.o')))==digest,path
    assert len(build['objectHashes'])==146
    if build['reusedObjectCount']:
        assert args.reuse_build is not None
        previous=args.reuse_build.resolve(strict=True);assert previous.is_relative_to(ROOT/'artifacts/th14')
        old_raw=read(previous/'build.json');old=json.loads(old_raw)
        assert sha(old_raw)==build['reuseBuildReportSha256']and old['flags']==build['flags']
        assert old['compilerVersion']==build['compilerVersion']and old['compiled']
        before=old['sourceBindings'];after=build['sourceBindings']
        cpp=lambda rows:{k:v['sha256']for k,v in rows.items()if Path(k).suffix in ('.cpp','.h','.hpp','.inc')}
        left,right=cpp(before),cpp(after);assert set(left)==set(right)
        changed={name for name in left if left[name]!=right[name]}
        assert all(Path(name).suffix=='.cpp'for name in changed)
        reused=build['reusedObjectHashes'];assert len(reused)==build['reusedObjectCount']
        assert set(build['objectHashes'])-set(reused)==changed
        for name,digest in reused.items():
            assert digest==old['objectHashes'][name]==build['objectHashes'][name]and left[name]==right[name]
            assert sha(read(previous/'source'/name))==left[name]
            obj=name.replace('/','_')+'.o'
            assert sha(read(previous/'objects'/obj))==digest
            assert os.path.samefile(previous/'objects'/obj,home/'browser-candidate/objects'/obj)
    for filename,field in [('th14-sdl.wasm','wasmSha256'),('th14-sdl.mjs','loaderSha256')]:
        raw=read(home/'browser-candidate'/filename)
        assert sha(raw)==build[field] and raw==read(home/'browser-runtime'/filename)
    assert build['wasmSha256']==package['wasmSha256']==routes['wasmSha256']==transport['wasmSha256']==served['wasmSha256']
    assert transport['verifiedTransport'] and transport['routes']==133 and len(transport['requests'])==21
    assert served['quietByDefault'] and served['actualServedWasmAndShaderAndHostBytesEqual']
    for request in served['requests']:
        if request['route']=='/__workspace/quiet-audio.js':continue
        row=routes['files'][request['route'].removeprefix('/')]
        assert request['bytes']==row['bytes'] and request['sha256']==row['sha256']
    assert len(package['generatedResourceAliases'])==28 and package['generatedResourceBytesAliased']==414850582
    assert not package['originalRetailFilesLinked'] and not package['originalAssetsCopied']
    for row in package['generatedResourceAliases']:
        assert os.path.samefile(home/'browser-runtime'/row['path'],ROOT/row['source'])
        assert (home/'browser-runtime'/row['path']).stat().st_size==row['bytes']
    courier=ROOT/'tools/tmp/github-source-release'
    for relative in ('th12_web/cpp/game/GameSession.cpp','th12_web/cpp/game/Replay.cpp'):
        raw=read(home/'browser-candidate/source'/relative)
        published=subprocess.check_output(['git','-C',str(courier),'show',args.expected_code_commit+':runtimes/th12/'+relative])
        assert raw==published
    for report in (build,package,routes,served):
        assert not report['browserAcceptance'] and not report['completeGame'] and not report['nativeEquivalent']
    result=dict(verifiedFrozenLocalCandidate=True,codeCommit=args.expected_code_commit,
        totalCppUnits=146,compiledCppUnits=build['compiledUnits'],reusedObjects=build['reusedObjectCount'],wasmBytes=build['wasmBytes'],wasmSha256=build['wasmSha256'],
        routeCount=133,httpChecks=21,observedUrl=served['url'],observedUtc=served['checkedUtc'],quietByDefault=True,
        generatedAssetAliases=28,generatedAssetLogicalBytes=414850582,
        currentBrowserRun=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=sha(Path(__file__).read_bytes()),bindings=bindings)
    if args.check:assert json.loads(args.output.read_text())==result
    else:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))

if __name__=='__main__':main()
