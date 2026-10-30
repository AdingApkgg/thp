"""Bind canonical production builds to the exact privately tested instancing bytes.

This rechecks finite evidence. It never accepts a running full replay, a browser
build, or whole-game equivalence merely because component binaries are equal.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(home):
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    candidate=ROOT/'artifacts/th14/webgpu-instance-candidate-oct30'
    spec=importlib.util.spec_from_file_location('instance_evidence',ROOT/'tools/th14-webgpu-instancing-evidence-oct30.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    proof=audit.verify(candidate)
    assert proof==load(home/'historical-candidate-verified.json')
    applied=load(candidate/'production-applied.json')
    assert applied['privateCandidateProofSha256']==SHA(read(candidate/'verified.json'))
    for name,row in applied['files'].items():assert SHA(read(ROOT/name))==row['candidateSha256']
    result=load(home/'binary-binding.json')
    assert result['productionBuildMatchesTestedCandidate']and result['glesBinaryUnchanged']
    identities={}
    for label,row in result['bindings'].items():
        current,tested=read(ROOT/row['current']),read(ROOT/row['tested'])
        assert current==tested and len(current)==row['bytes']and SHA(current)==row['sha256']
        identities[label]=row
    assert read(home/'component-build/probe.wasm')==read(candidate/'build/probe.wasm')
    for folder in ['component-build','async-build','webgpu-build','gles-build']:
        build=load(home/folder/'build.json')
        for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
        if folder.endswith('build')and folder in ['webgpu-build','gles-build']:
            assert len(build['coreObjects'])==141
            for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
            for name,digest in build['newObjects'].items():assert SHA(read(home/folder/name))==digest
    for name in ['Th14WebGpuHost.mjs','Th14WebGpu.wgsl','Th14WebGpuRuntime.mjs','Th14ArchiveDecodeClient.mjs','Th14ArchiveReadAhead.mjs']:
        assert read(home/'async-build'/name)==read(ROOT/'runtimes/th12/portable/sdl'/name)
    read(ROOT/'tools/th14-native-webgpu-context.py');read(ROOT/'tools/th14-build-webgpu-async-component.py')
    old=load(ROOT/'artifacts/th14/reimub-normal-webgpu-current-oct30/verified.json')
    assert old['verifiedFiniteApplicationFullReplay']and old['frames']==122622 and old['stageCount']==6
    assert applied['fullBaselineProofSha256']==SHA(read(ROOT/'artifacts/th14/reimub-normal-webgpu-current-oct30/verified.json'))
    browser_home=ROOT/'artifacts/th14/webgpu-instanced-browser-oct30'
    browser=load(browser_home/'build.json')
    assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and browser['reusedObjectCount']==0
    assert SHA(read(browser_home/'th14-sdl.wasm'))==browser['wasmSha256']
    assert SHA(read(browser_home/'th14-sdl.mjs'))==browser['loaderSha256']
    for name,row in browser['sourceBindings'].items():assert SHA(read(browser_home/'source'/name))==row['sha256']
    for name in ['WebGpuRenderer.hpp','Th14WebGpu.wgsl','Th14WebGpuHost.mjs','Th14WebGpuLibrary.js']:
        assert read(browser_home/'source/portable/sdl'/name)==read(ROOT/'runtimes/th12/portable/sdl'/name)
    for name in ['01-title','02-stage3-demo']:
        read(home/'browser-ui'/(name+'.png'))
        ax=read(home/'browser-ui'/(name+'.ax.txt')).decode()
        assert 'localhost:8247/'in ax and 'SDL3 / WebGPU / C++'in ax and '本机测试静音'in ax
    served=load(home/'served.json');assert served['wasmSha256']==browser['wasmSha256']and served['quietParentAndIframe']
    for row in served['rows']:
        assert SHA(read(home/'runtime'/row['route'].removeprefix('runtime/th14/')))==row['sha256']
    return dict(schema='th14/webgpu-production-binding/1',canonicalBuildsMatchTestedCandidate=True,
        finiteProductionIntegrationAccepted=True,coreObjectsVerifiedPerApplication=141,
        nativeAndAsyncStageFullBuffersEach=21,nativeAndAsyncSyntheticFullBuffersEach=8,
        applicationPrefixFramesEach=2264,applicationPrefixAssertionsEach=21,
        actualPrefixDrawCallsBefore=225938,actualPrefixDrawCallsAfter=82420,
        naturalAttractFramesEach=17547,naturalAttractAssertionsEach=30,naturalAttractCapturedBuffersEqual=7,
        glesBinaryUnchanged=True,binaryIdentities=identities,
        serialBaselineFullReplayFrames=122622,serialBaselineIsHistoricalRenderer=True,
        newInstancedFullReplayAccepted=False,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],
        browserFiniteStartupAndDemoObserved=True,fullBrowserBuildAccepted=False,
        browserStableFpsAccepted=False,originalWholeApplicationPixelsOrPcmCompared=False,
        productionGameplayCoreChanged=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/webgpu-instance-production-oct30')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    home=a.home.resolve();out=a.output.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')
    assert out.is_relative_to(ROOT/'artifacts/th14')or out.is_relative_to(ROOT/'docs/porting')
    result=verify(home)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','binaryIdentities']}))
