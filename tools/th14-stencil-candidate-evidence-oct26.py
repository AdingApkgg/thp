"""Verify the current local candidate package; no browser execution is asserted."""
from pathlib import Path
import argparse
import hashlib
import json
import os

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=ROOT/'artifacts/th14/stencil-clear-oct26';bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def file_hash(path):
        with path.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=digest);return digest
    def load(path):return json.loads(read(path))
    build_home=home/'browser-candidate';runtime=home/'browser-runtime';launcher=home/'launcher-candidate'
    build=load(build_home/'build.json');package=load(runtime/'package-report.json');routes=load(launcher/'launcher-report.json');transport=load(launcher/'transport.json')
    assert build['compiled']and build['basePublishedCommit']=='1776db96c0655bf0c941a715c5aa30f4c4c00285'
    assert build['sourceUnits']==build['reusedObjectCount']==146 and build['compiledUnits']==0
    assert build['rootUnrelatedResourceCryptExcluded']and not build['retailAssetsIncluded']
    assert build['actualSdlPort']and build['asyncify']and not build['browserAcceptance']
    old_home=ROOT/'artifacts/th14/webgpu-js-host-oct26/browser-candidate-final';old=load(old_home/'build.json')
    assert SHA(read(old_home/'build.json'))==build['reuseBuildReportSha256']
    assert build['flags']==old['flags']and build['compilerVersion']==old['compilerVersion']
    cpp=lambda inventory:{path:row['sha256']for path,row in inventory.items()if Path(path).suffix in['.cpp','.h','.hpp','.inc']}
    assert cpp(build['sourceBindings'])==cpp(old['sourceBindings'])
    for path,row in build['sourceBindings'].items():assert file_hash(build_home/'source'/path)==row['sha256']
    for path,digest in build['reusedObjectHashes'].items():
        name=path.replace('/','_')+'.o';current=build_home/'objects'/name;previous=old_home/'objects'/name
        assert os.path.samefile(current,previous)and file_hash(current)==old['objectHashes'][path]==digest
    assert build['wasmSha256']==old['wasmSha256']==file_hash(build_home/'th14-sdl.wasm')=='3786901cbe373d221b14f02bcb3b1fa77901512195a09ba080669753a915018c'
    assert build['loaderSha256']==file_hash(build_home/'th14-sdl.mjs')
    host_digest=file_hash(ROOT/'runtimes/th12/portable/sdl/Th14WebGpuHost.mjs')
    assert file_hash(build_home/'Th14WebGpuHost.mjs')==host_digest
    assert build['sourceBindings']['portable/sdl/Th14WebGpuHost.mjs']['sha256']==host_digest
    assert package['prepared']and package['noDiagnosticGameControlExports']and not package['originalRetailFilesLinked']and not package['originalAssetsCopied']
    assert package['buildSha256']==SHA(read(build_home/'build.json'))and package['wasmSha256']==build['wasmSha256']
    for name,row in package['files'].items():assert file_hash(runtime/name)==row['sha256']and(runtime/name).stat().st_size==row['bytes']
    assert package['generatedResourceBytesAliased']==414850582 and len(package['generatedResourceAliases'])==28
    for row in package['generatedResourceAliases']:
        assert os.path.samefile(runtime/row['path'],ROOT/row['source'])
        assert file_hash(ROOT/row['source'])==row['sha256']
    assert file_hash(runtime/'Th14WebGpuHost.mjs')==host_digest
    assert routes['prepared']and routes['frozenLauncherReused']and not routes['payloadFilesCopied']and not routes['originalFilesLinked']
    assert routes['runtimeReportSha256']==SHA(read(runtime/'package-report.json'))
    assert routes['physicalBytesWritten']==103342 and routes['existingPayloadBytesReferenced']==510696486
    for name,row in routes['files'].items():assert file_hash(ROOT/row['path'])==row['sha256']and(ROOT/row['path']).stat().st_size==row['bytes']
    assert transport['verifiedTransport']and transport['routes']==133 and len(transport['requests'])==21
    assert transport['quietByDefault']and transport['reportSha256']==SHA(read(launcher/'launcher-report.json'))
    assert transport['contractChecks']==['validateHostManifest','validateReleaseCatalog','validatePackageDescriptor']
    served=load(home/'served-current.json');assert served['currentProductionHostBytesEqual']and served['quietHtmlInjected']and served['httpStatus']==200 and served['hostSha256']==host_digest
    for path,digest in transport['sourceBindings'].items():assert isinstance(digest,str)and file_hash(ROOT/path)==digest
    result=dict(verifiedLocalCurrentCandidate=True,basePublishedCommit=build['basePublishedCommit'],reusedCppObjects=146,compiledCppUnits=0,
        allCppInputHashesUnchanged=True,fullGameWasmByteIdentical=True,currentProductionHostHashBound=True,currentHostSha256=host_digest,
        generatedResourceBytesAliased=414850582,generatedResourceAliases=28,launcherMetadataBytesWritten=103342,existingPayloadBytesReferenced=510696486,
        launcherRoutes=133,httpChecks=21,quietByDefault=True,url=served['url'],servedAtUtc=served['checkedUtc'],
        originalRetailFilesLinked=False,payloadFilesDuplicated=False,defaultPreviewChanged=False,
        browserRun=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Fresh browser-targeted link from published1776db9 with146 hash-identical C++ objects and actual SDL port, plus current stencil host. Managed Runtime packages only generated immutable assets by aliases;133 Launcher routes and21 real HTTP/contract checks verified. A direct local HTTP fetch matches the current host. No browser/DOM/window input, presentation, IndexedDB, physical audio or whole-game acceptance.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in['verifiedLocalCurrentCandidate','reusedCppObjects','fullGameWasmByteIdentical','generatedResourceBytesAliased','launcherRoutes','httpChecks','url','browserAcceptance']}))


if __name__=='__main__':main()
