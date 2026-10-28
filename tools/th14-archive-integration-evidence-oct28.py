"""Verify the frozen, finite TH14 browser archive-worker integration evidence."""
from pathlib import Path
import argparse,hashlib,json,subprocess,struct
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def jpeg_size(raw):
    assert raw[:2]==b'\xff\xd8';cursor=2
    while cursor<len(raw):
        assert raw[cursor]==255
        while raw[cursor]==255:cursor+=1
        marker=raw[cursor];cursor+=1
        if marker in (1,*range(0xd0,0xda)):continue
        length=struct.unpack_from('>H',raw,cursor)[0];assert length>=2 and cursor+length<=len(raw)
        if marker in (0xc0,0xc1,0xc2):
            height,width=struct.unpack_from('>2H',raw,cursor+3);return width,height
        cursor+=length
    raise AssertionError('JPEG dimensions missing')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=R/'docs/porting/th14-archive-integration-verified-oct28.json')
    a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    H=R/'artifacts/th14/native-frame-readback-oct28';D=H/'worker-runtime-delivery-v2';B=D/'browser-candidate'
    build=load(B/'build.json');assert build['compiled'] and build['sourceUnits']==build['compiledUnits']==146
    assert build['reusedObjectCount']==0 and '-DTH14_ARCHIVE_WORKER=1' in build['flags']
    assert SHA(read(B/'build-tool.py'))==build['toolSha256']
    for name,row in build['sourceBindings'].items():assert SHA(read(B/'source'/name))==row['sha256'],name
    for name,digest in build['objectHashes'].items():assert SHA(read(B/'objects'/(name.replace('/','_')+'.o')))==digest,name
    assert build['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    assert build['rootUnrelatedResourceCryptExcluded'] and not build['retailAssetsIncluded']
    assert SHA(read(B/'th14-sdl.wasm'))==build['wasmSha256']
    assert SHA(read(B/'th14-sdl.mjs'))==build['loaderSha256']
    worker=load(B/'archive-worker/build.json');assert SHA(read(B/'archive-worker/build.json'))==build['archiveWorkerBuildSha256']
    assert worker['browserRuntimeModules'] and worker['compiled']
    for name,row in build['archiveWorkerFiles'].items():
        assert SHA(read(B/name))==SHA(read(B/'archive-worker'/name))==row['sha256']
    kernel=load(B/'archive-worker/check.json')
    assert kernel['passed'] and kernel['archiveEntries']==227 and kernel['directByteComparison']
    assert kernel['comparedDecodedBytes']==253480939 and kernel['reverseOrderComparisons']==227
    runtime=load(H/'worker-runtime-component-v2/report.json')
    assert runtime['passed'] and runtime['actualProductionRuntimeAndBrowserWorkerSource']
    for key in ['cpuFinishedDuringPendingFrame','callbackWaitedForFrame','staleCallbackDeliveredOnceForCppTokenCleanup',
                'cacheClearedAfterCallback','workerFailureDeliveredToCppStatus','resumedGenerationPassed']:assert runtime[key]
    fixture=load(H/'background-resource-compare-v3/build.json');resources=load(H/'background-resource-compare-v3/check.json')
    assert fixture['browserBuildSha256']==resources['browserBuildSha256']==SHA(read(B/'build.json'))
    assert len(fixture['objectBindings'])==141 and fixture['mainGameResourceObjectUsed']
    assert resources['passed'] and resources['cases']==42 and len(resources['rows'])==42
    assert resources['cacheReads']==resources['cacheCopies']==534 and resources['failedBatchCannotSilentlyFallback']
    assert all(row['allParsedValuesAndBytesEqual'] for row in resources['rows'])
    native=load(H/'archive-native-compat-v2/report.json');assert native['passed'] and len(native['rows'])==2
    assert all(row['byteIdentical'] and row['sha256']==row['referenceSha256'] for row in native['rows'])
    for name,digest in native['sourceBindings'].items():assert SHA(read(R/name))==digest
    native_gpu=load(H/'worker-compatible-webgpu-build/build.json');assert native_gpu['compiled']
    native_wasm=H/'worker-compatible-webgpu-build/application.wasm';assert SHA(read(native_wasm))==native_gpu['wasmSha256']
    node='C:/nvm4w/nodejs/node.exe'
    imports=json.loads(subprocess.check_output([node,'-e',
        'const f=require("fs");console.log(JSON.stringify(WebAssembly.Module.imports(new WebAssembly.Module(f.readFileSync(process.argv[1])))));',str(native_wasm)],text=True))
    assert not any(row['name'].startswith('th14_webgpu_archive_') for row in imports)
    package=load(D/'browser-runtime/package-report.json');routes=load(D/'launcher-candidate/launcher-report.json')
    transport=load(D/'launcher-candidate/transport.json');served=load(D/'served-current.json')
    assert transport['verifiedTransport'] and transport['routes']==139 and len(transport['requests'])==27
    assert served['actualServedMainAndWorkerBytesEqual'] and served['quietInjectedIntoParentAndIframe']
    assert build['wasmSha256']==package['wasmSha256']==routes['wasmSha256']==transport['wasmSha256']==served['wasmSha256']
    for row in served['requests']:
        expected=routes['files'][row['route'].removeprefix('/')];assert row['sha256']==expected['sha256'] and row['bytes']==expected['bytes']
    assert package['generatedResourceBytesAliased']==414850582 and len(package['generatedResourceAliases'])==28
    assert not package['originalAssetsCopied'] and not package['originalRetailFilesLinked']
    pictures=[];ui=H/'worker-browser-ui-v2'
    for name in ['title','normal-rank','normal-reimu-selection','normal-reimu-a-weapon','normal-first-stage','ordinary-pause','ordinary-resumed']:
        raw=read(ui/(name+'.jpg'));width,height=jpeg_size(raw);assert width>=640 and height>=480
        pictures.append(dict(label=name,width=width,height=height,sha256=SHA(raw)))
    for name in ['normal-first-stage-ax.txt','ordinary-pause-ax.txt','ordinary-resumed-ax.txt']:
        ax=read(ui/name).decode();assert '127.0.0.1:8234/' in ax and '本机测试静音' in ax and 'WebGPU / C++' in ax
    logs=load(ui/'loading-console.json')
    assert sum(row['message']=='[loading14] initial worker ready; control callbacks attached' for row in logs)>=2
    for number,chunks in [(9,13),(4,5),(6,2),(10,3),(11,16)]:
        assert any(row['message']==f'[loading14] file {number} ready after {chunks} chunk callbacks' for row in logs)
    for name in ['th14-archive-runtime-check-oct28.mjs','th14-background-resource-build-oct28.py',
        'th14-background-resource-check-oct28.mjs','th14-archive-native-compat-oct28.py',
        'th14-package-webgpu-candidate.py','th14-webgpu-launcher-transport-check.mjs',
        'th14-archive-worker-prototype-build-oct27.py','th14-archive-worker-prototype-check-oct27.mjs']:read(R/'tools'/name)
    read(D/'verify-preview.py')
    result=dict(verifiedFiniteArchiveIntegration=True,codeBase=build['basePublishedCommit'],
        compiledCppUnits=146,mainWasmBytes=build['wasmBytes'],mainWasmSha256=build['wasmSha256'],
        workerWasmBytes=worker['wasmBytes'],workerWasmSha256=worker['wasmSha256'],
        independentDecoderArchiveEntries=227,directDecodedByteComparisons=253480939,
        productionCppParsedResourceCases=42,workerCacheReadsAndCopies=534,
        asyncFrameFenceAndCancellationControlsPassed=True,nativeDisabledObjectsByteIdentical=2,
        nativeWebGpuHostRelinkedWithoutArchiveImports=True,routeCount=139,httpChecks=27,
        actualBrowserObserved=['startup','normal difficulty','Reimu A selection','ordinary first stage','pause','resume and move'],
        uiPictures=pictures,observedUrl=served['url'],quietByDefault=True,initialStageArchiveWorkerIntegrated=True,
        wholeBrowserWorkerSchedulingTraceCaptured=False,fixedFrameOrVmAgeCompensationAdded=False,
        firstOriginalGameplayFrameStrictDifferenceClosed=False,browserReplaySaveReloadAccepted=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    if a.check:assert json.loads(a.output.read_bytes())==result
    else:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('bindings','uiPictures')}))
if __name__=='__main__':main()
