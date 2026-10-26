"""Bind the freshly compiled Bgrx8 candidate to finite controls and HTTP checks.

This is package and transport evidence, without browser execution or acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
BASE = '96bf57c97d41d583a07c5c30a24dcf4b94d93990'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    home = ROOT / 'artifacts/th14/bgrx-raster-oct27'
    build_home = home / 'browser-candidate-final'
    runtime = home / 'browser-runtime'
    launcher = home / 'launcher-candidate'
    bindings = {}

    def digest(path):
        with path.open('rb') as stream:
            value = hashlib.file_digest(stream, 'sha256').hexdigest()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=path.stat().st_size, sha256=value)
        return value

    def load(path):
        digest(path)
        return json.loads(path.read_bytes())

    finite = load(ROOT / 'docs/porting/th14-bgrx-raster-verified-oct27.json')
    assert finite['verifiedFiniteBgrxRasterIncrement'] and finite['allCanonicalBuffersExact']
    assert finite['halCases'] == finite['cppJsCases'] == finite['nativeCppCases'] == 1344
    assert finite['stageRegressionFrames'] == 21 and finite['d3dxRegressionCases'] == 8 and finite['stencilRegressionCases'] == 96
    assert finite['verifierSha256'] == digest(ROOT / 'tools/th14-bgrx-raster-evidence-oct27.py')
    for path, row in finite['bindings'].items():
        assert digest(ROOT / path) == row['sha256'], path

    build = load(build_home / 'build.json')
    package = load(runtime / 'package-report.json')
    routes = load(launcher / 'launcher-report.json')
    transport = load(launcher / 'transport.json')
    assert build['compiled'] and build['basePublishedCommit'] == BASE
    assert build['sourceUnits'] == build['compiledUnits'] == 146 and build['reusedObjectCount'] == 0
    assert build['reuseBuildReportSha256'] is None and not build['reusedObjectHashes']
    assert build['actualSdlPort'] and build['asyncify'] and build['rootUnrelatedResourceCryptExcluded']
    assert not build['retailAssetsIncluded'] and not build['browserAcceptance']
    for path, row in build['sourceBindings'].items():
        assert digest(build_home / 'source' / path) == row['sha256'], path
    for path, value in build['objectHashes'].items():
        assert digest(build_home / 'objects' / (path.replace('/', '_') + '.o')) == value, path
    header = 'runtimes/th12/portable/sdl/WebGpuRenderer.hpp'
    assert digest(ROOT / header) == digest(build_home / 'source/portable/sdl/WebGpuRenderer.hpp') == digest(home / 'final-build/src/WebGpuRenderer.hpp')
    assert build['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    assert build['wasmSha256'] == digest(build_home / 'th14-sdl.wasm')
    assert build['loaderSha256'] == digest(build_home / 'th14-sdl.mjs')
    old = load(ROOT / 'artifacts/th14/stencil-clear-oct26/browser-candidate/build.json')
    assert build['wasmSha256'] != old['wasmSha256'], 'New C++ graphics must not inherit the older Wasm'
    assert build['toolSha256'] == digest(build_home / 'build-tool.py') == digest(ROOT / 'tools/th14-build-webgpu-release.py')
    assert build['storageToolSha256'] == digest(build_home / 'storage-tool.py') == digest(ROOT / 'tools/th14-test-storage.py')
    storage = load(home / 'storage-race-control/report.json')
    assert storage['passed'] and storage['vanishedTemporaryEntryTolerated'] and storage['permissionErrorRejected']
    assert storage['maximumCaseStillRejects'] and storage['freeReserveStillRejects'] and storage['retainedContentUnchanged']
    assert storage['storageToolSha256'] == build['storageToolSha256']
    assert storage['toolSha256'] == digest(ROOT / 'tools/th14-storage-budget-check-oct27.py')

    assert package['prepared'] and package['noDiagnosticGameControlExports']
    assert package['buildSha256'] == digest(build_home / 'build.json') and package['wasmSha256'] == build['wasmSha256']
    assert not package['originalRetailFilesLinked'] and not package['originalAssetsCopied']
    assert package['generatedResourceBytesAliased'] == 414850582 and len(package['generatedResourceAliases']) == 28
    for name, row in package['files'].items():
        assert digest(runtime / name) == row['sha256'] and (runtime / name).stat().st_size == row['bytes'], name
    for row in package['generatedResourceAliases']:
        assert os.path.samefile(runtime / row['path'], ROOT / row['source'])
        assert digest(ROOT / row['source']) == row['sha256']
    for name in ['Th14WebGpuHost.mjs', 'Th14WebGpu.wgsl', 'Th14WebGpuResample.wgsl']:
        assert digest(runtime / name) == digest(ROOT / 'runtimes/th12/portable/sdl' / name)
    assert routes['prepared'] and routes['frozenLauncherReused'] and not routes['payloadFilesCopied'] and not routes['originalFilesLinked']
    assert routes['runtimeReportSha256'] == digest(runtime / 'package-report.json')
    for row in routes['files'].values():
        assert digest(ROOT / row['path']) == row['sha256'] and (ROOT / row['path']).stat().st_size == row['bytes']
    assert transport['verifiedTransport'] and transport['routes'] == 133 and len(transport['requests']) == 21
    assert transport['quietByDefault'] and transport['reportSha256'] == digest(launcher / 'launcher-report.json')
    assert transport['wasmSha256'] == build['wasmSha256']
    assert transport['contractChecks'] == ['validateHostManifest', 'validateReleaseCatalog', 'validatePackageDescriptor']
    for path, value in transport['sourceBindings'].items():
        assert digest(ROOT / path) == value
    served = load(home / 'served-current.json')
    assert served['httpStatus'] == 200 and served['quietHtmlInjected'] and served['currentProductionHostBytesEqual']
    assert served['hostSha256'] == digest(ROOT / 'runtimes/th12/portable/sdl/Th14WebGpuHost.mjs')
    assert served['wasmSha256'] == build['wasmSha256'] and served['wasmBytesEqual']
    result = dict(verifiedFreshBgrxCandidate=True, basePublishedCommit=BASE,
        compiledCppUnits=146, reusedCppObjects=0, currentCppGraphicsHashBound=True,
        wasmBytes=build['wasmBytes'], wasmSha256=build['wasmSha256'], olderWasmNotReused=True,
        finiteHalCases=1344, buffersPerBackend=4032, comparedBytesPerBackend=4128768,
        stageRegressionFrames=21, d3dxRegressionCases=8, stencilRegressionCases=96,
        generatedResourceBytesAliased=414850582, generatedResourceAliases=28,
        launcherMetadataBytesWritten=routes['physicalBytesWritten'], existingPayloadBytesReferenced=routes['existingPayloadBytesReferenced'],
        launcherRoutes=133, httpChecks=21, quietByDefault=True, url=served['url'], servedAtUtc=served['checkedUtc'],
        continuousStorageChecks=True, vanishedCompilerTemporaryHandled=True, bothBudgetGatesStillReject=True,
        originalRetailFilesLinked=False, payloadFilesDuplicated=False, defaultPreviewChanged=False,
        browserRun=False, browserAcceptance=False, completeGame=False, nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings,
        scope='Fresh compilation of all146 C++ units from published96bf57c and declared TH14 overlays, actual SDL3/Asyncify, current Bgrx8 header bound to finite controls. Generated resources aliased;133 routes and21 real HTTP/contract checks pass. Direct HTTP verifies current host and full Wasm bytes. No browser execution, presentation, input, persistence, physical audio, original ordinary Application or whole-game acceptance.')
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14') or output.is_relative_to(ROOT / 'docs/porting')
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: result[key] for key in ['verifiedFreshBgrxCandidate', 'compiledCppUnits', 'wasmSha256', 'launcherRoutes', 'httpChecks', 'url', 'browserAcceptance']}))


if __name__ == '__main__':
    main()
