"""Verify backend identity, frozen delivery files and retained real HTTP checks.

Does not open a browser or accept gameplay, GPU presentation or persistence.
"""
from pathlib import Path
import argparse, ast, hashlib, json, os, subprocess

R = Path(__file__).resolve().parents[1]
G = R / 'artifacts/th14/gles-clip-portable-nov04'
SHA = lambda b: hashlib.sha256(b).hexdigest()

def verify():
    bindings = {}
    def bind(path):
        path = path.resolve(strict=True); assert path.is_relative_to(R)
        with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        row = dict(bytes=path.stat().st_size, sha256=digest)
        bindings[path.relative_to(R).as_posix()] = row
        return row
    def raw(path):
        row = bind(path); b = path.read_bytes(); assert SHA(b) == row['sha256']; return b
    def load(path): return json.loads(raw(path))
    def check(path, row):
        actual = bind(path); assert actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], str(path)
    tested_packager = raw(G/'delivery-package-tool-tested-nov05.py')
    public_packager = raw(R/'tools/th14-package-renderer-candidate-nov05.py')
    assert public_packager == tested_packager.replace(b'\r\n', b'\n').replace(b'\r', b'\n').rstrip(b'\n') + b'\n'
    assert ast.dump(ast.parse(public_packager.decode())) == ast.dump(ast.parse(tested_packager.decode()))
    result = []
    for backend, build_dir, runtime_dir, routes, expected_wasm in [
        ('gles', 'browser-gles-nov05', 'delivery-gles-v2-nov05', 134, '0a9750bfe24129ec6005b197fe599b49c2adb62652e175c85e8c0b479f616794'),
        ('webgpu', 'browser-retry1-nov05', 'delivery-webgpu-retry1-nov05', 139, '340aad1aeac70cda36f084a3bf567cc2f31924feb10e9e09feafd875d0d0049b'),
    ]:
        build_home = G / build_dir; runtime_home = G / runtime_dir
        launcher_home = G / ('launcher-' + backend + '-nov05')
        build = load(build_home / 'build.json'); runtime = load(runtime_home / 'package-report.json')
        launcher = load(launcher_home / 'launcher-report.json'); http = load(G / ('transport-' + backend + '-nov05.json'))
        assert build['compiledUnits'] == build['sourceUnits'] == 146 and build['reusedObjectCount'] == 0
        assert build['wasmSha256'] == runtime['wasmSha256'] == launcher['wasmSha256'] == http['wasmSha256'] == expected_wasm
        assert runtime['buildSha256'] == bind(build_home / 'build.json')['sha256']
        assert launcher['runtimeReportSha256'] == bind(runtime_home / 'package-report.json')['sha256']
        assert http['reportSha256'] == bind(launcher_home / 'launcher-report.json')['sha256']
        assert runtime['backend'] == launcher['backend'] == http['backend'] == backend
        assert runtime['backendBoundToCompilerFlagsAndExports']
        assert ('-DTH14_WEBGPU_BACKEND=1' in build['flags']) == (backend == 'webgpu')
        assert ('-DTH14_ARCHIVE_WORKER=1' in build['flags']) == (backend == 'webgpu')
        assert runtime['backgroundArchiveIntegration'] == runtime['frameAndWorkerCallbacksSerialized'] == (backend == 'webgpu')
        for item in [build, runtime, launcher, http]:
            assert not item['browserAcceptance'] and not item['completeGame'] and not item['nativeEquivalent']
        for name, row in build['sourceBindings'].items(): check(build_home / 'source' / name, row)
        for name in ['Renderer.cpp','Renderer.hpp','Shaders.hpp','Th14RenderMath.hpp']:
            rel = 'portable/sdl/' + name
            assert build['sourceBindings'][rel]['sha256'] == bind(R / 'runtimes/th12' / rel)['sha256']
        for name, row in runtime['files'].items(): check(runtime_home / name, row)
        for name, row in runtime['sourceBindings'].items(): check(R / name, row)
        assert runtime['toolSha256'] == SHA(tested_packager)
        assert launcher['toolSha256'] == bind(R / 'tools/th14-prepare-renderer-launcher-nov05.py')['sha256']
        for name, digest in http['sourceBindings'].items(): assert bind(R / name)['sha256'] == digest
        for name, row in launcher['files'].items(): check(R / row['path'], row)
        for name, row in launcher['sourceBindings'].items(): check(R / name, row)
        assert http['verifiedTransport'] and http['routes'] == len(launcher['files']) == routes
        assert http['quietByDefault'] and len(http['requests']) == 27 and len(http['contractChecks']) == 3
        assert any(x.get('localPassthrough') for x in http['requests'])
        assert sum(bool(x.get('unusedBackendModuleAbsent')) for x in http['requests']) == (5 if backend == 'gles' else 0)
        managed = load(runtime_home / 'manifest.json')
        assert managed['execution']['backend'] == backend
        assert managed['execution']['kind'] == 'th14-sdl3-' + backend + '-candidate'
        assert managed['version'] == '1.00b-' + backend + '-candidate'
        aliases = runtime['generatedResourceAliases']; assert len(aliases) == 28
        for row in aliases:
            assert os.path.samefile(R / row['source'], runtime_home / row['path'])
        assert runtime['generatedResourceBytesAliased'] == sum(row['bytes'] for row in aliases) == 414850582
        assert not runtime['originalRetailFilesLinked'] and not runtime['originalAssetsCopied']
        assert not launcher['payloadFilesCopied'] and not launcher['originalFilesLinked']
        assert launcher['physicalBytesWritten'] < 128 * 1024
        metadata_payload_bytes = sum(p.stat().st_size for p in (launcher_home/'metadata').rglob('*') if p.is_file())
        assert metadata_payload_bytes == launcher['physicalBytesWritten']
        launcher_total_bytes = sum(p.stat().st_size for p in launcher_home.rglob('*') if p.is_file())
        abi = runtime['abi']; names = {row['name'] for row in abi['exports']}
        for symbol in ['th14_webgpu_invoke','th14_webgpu_frame']:
            assert (symbol in names) == (backend == 'webgpu')
        result.append(dict(backend=backend, wasmSha256=expected_wasm, compiledUnits=146, routes=routes,
            httpRequests=27, launcherContracts=3, generatedImmutableResourceAliases=28,
            generatedResourceBytesReferenced=414850582, largeResourceBytesCopied=0,
            launcherMetadataPayloadBytes=metadata_payload_bytes, launcherTotalBytesIncludingReport=launcher_total_bytes,
            backgroundArchiveIntegration=backend=='webgpu',
            frameAndWorkerCallbacksSerialized=backend=='webgpu', browserAcceptance=False))
    baseline_home = G / 'delivery-gles-legacy-control-nov05'
    baseline = load(baseline_home / 'package-report.json')
    baseline_manifest = load(baseline_home / 'manifest.json')
    assert baseline['wasmSha256'] == result[0]['wasmSha256']
    assert baseline_manifest['execution']['kind'] == 'th14-sdl3-webgpu-candidate'
    assert baseline_manifest['version'] == '1.00b-webgpu-candidate'
    assert 'backend' not in baseline_manifest['execution']
    assert baseline['toolSha256'] == bind(R / 'tools/th14-package-webgpu-candidate.py')['sha256']
    assert not any(row['name'].startswith('th14_webgpu_') for row in baseline['abi']['exports'])
    for name, row in baseline['files'].items():check(baseline_home / name, row)
    negative = load(G / 'backend-declaration-controls-nov05/report.json')
    assert negative['passed'] and len(negative['cases']) == 2
    assert negative['toolSha256'] == SHA(tested_packager)
    for case in negative['cases']:
        assert case['actualBackend'] != case['declaredBackend'] and case['exitCode'] != 0
        log = G / 'backend-declaration-controls-nov05' / case['actualBackend'] / 'process.log'
        assert bind(log)['sha256'] == case['logSha256']
    entry = load(G / 'active-preview-gles-nov05.json')
    assert entry['verifiedLiveEntryTransport'] and entry['backend'] == 'gles' and len(entry['checks']) == 5
    assert entry['wasmSha256'] == result[0]['wasmSha256']
    assert entry['launcherReportSha256'] == bind(G / 'launcher-gles-nov05/launcher-report.json')['sha256']
    assert any(x['quietHtml'] for x in entry['checks'])
    # This is a retained response check, not a claim that its process is still live.
    for case in entry['checks']:
        assert case['status'] == 200
        if not case['quietHtml']:
            route = json.loads((G / 'launcher-gles-nov05/launcher-report.json').read_bytes())['files'][case['path']]
            assert case['sha256'] == route['sha256'] and case['bytes'] == route['bytes']
    protected = {
        'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45',
        'artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
    for name, digest in protected.items(): assert bind(R / name)['sha256'] == digest
    return dict(schema='th14/renderer-delivery/1', verifiedFiniteDeliveryEvidence=True, profiles=result,
        legacyGlesPackageMislabelReproduced=True, backendMismatchControlsRejected=2,
        packagerPublicationOnlyLineEndingsNormalized=True, packagerTestedAndPublishedAstEqual=True,
        testedPackagerSha256=SHA(tested_packager), publishedPackagerSha256=SHA(public_packager),
        liveEntryTransportObserved=True, previewBackend='gles',
        previewUrl='http://localhost:8208/?game=th14', quietPolicyVerified=True, browserWindowObserved=False,
        productionGameplayChanged=False, rendererMathChanged=False, browserAcceptance=False, persistenceAccepted=False,
        wholeOriginalFramebufferOrPcmAccepted=False, completeGame=False, nativeEquivalent=False,
        limits=['Real HTTP and static module contracts only. No browser, DOM, GPU presentation, input, IDB reload or offline acceptance.',
                'Generated fonts/music share existing immutable files; the byte count is referenced size, not new disk allocation.',
                'The Launcher physicalBytesWritten advisory counts metadata payloads before its own report; both payload and actual total bytes are reported separately here.',
                'GLES uses normal SDL callbacks and has no background archive integration; it does not inherit WebGPU serialization acceptance.',
                'The retained five-response entry check does not prove the preview process is still running.'],
        verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true')
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting')or out.is_relative_to(R/'artifacts/th14')
    value=verify()
    if a.check:assert json.loads(out.read_bytes())==value
    else:
        assert not out.exists();out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(verifiedFiniteDeliveryEvidence=True,backends=[x['backend']for x in value['profiles']],routes=[x['routes']for x in value['profiles']],httpRequests=54,browserAcceptance=False)))
