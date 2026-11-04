"""Check frozen TH14 packaging provenance and retained HTTP results, without UI."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'artifacts/th14/scene-camera-read-job-nov04'
CORE = '51fcb47992be0af65777d2ea87e9e409be6cc641'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def evidence():
    bindings = {}

    def read(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(ROOT)
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    def bound(path, row):
        raw = read(path)
        assert len(raw) == row['bytes'] and SHA(raw) == row['sha256'], str(path)
        return raw

    courier = ROOT / 'tools/tmp/github-source-release'
    git = lambda *args: subprocess.check_output(['git', '-C', str(courier), *args])
    browser_home = HOME / 'browser'
    runtime_home = HOME / 'delivery-retry1'
    browser = load(browser_home / 'build.json')
    runtime = load(runtime_home / 'package-report.json')
    launcher_path = HOME / 'delivery-launcher/launcher-report.json'
    launcher = load(launcher_path)
    transport = load(HOME / 'delivery-transport.json')
    assert browser['compiled'] and browser['compiledUnits'] == browser['sourceUnits'] == 146
    assert browser['reusedObjectCount'] == 0
    for item in [browser, runtime, launcher, transport]:
        assert not item['browserAcceptance'] and not item['completeGame'] and not item['nativeEquivalent']
        assert item['wasmSha256'] == browser['wasmSha256']
    assert runtime['prepared'] and launcher['prepared'] and transport['verifiedTransport']
    assert runtime['buildSha256'] == SHA(read(browser_home / 'build.json'))
    assert runtime['toolSha256'] == SHA(read(ROOT / 'tools/th14-package-webgpu-candidate.py'))
    for name, row in runtime['sourceBindings'].items():
        bound(ROOT / name, row)
    for name, row in runtime['files'].items():
        bound(runtime_home / name, row)
    for name, row in browser['sourceBindings'].items():
        bound(browser_home / 'source' / name, row)
    ordinary = load(HOME / 'session-build/ordinary/observer-build.json')
    core_bindings = {**ordinary['sourceHashes'], **ordinary['headerHashes']}
    for name, digest in core_bindings.items():
        assert browser['sourceBindings'][name]['sha256'] == digest
    for name in ['SceneCamera.cpp', 'SceneCameraReadJobTh14.hpp', 'GameBattle.cpp', 'GameBattle.hpp']:
        source_name = 'th12_web/cpp/game/' + name
        published = git('show', CORE + ':runtimes/th12/' + source_name)
        assert SHA(published) == browser['sourceBindings'][source_name]['sha256']
    assert runtime['frozenPlatformCommit'] == browser['basePublishedCommit']
    assert git('cat-file', '-t', runtime['frozenPlatformCommit']).strip() == b'commit'
    assert len(runtime['frozenPlatformBindings']) == 8
    for name, row in runtime['frozenPlatformBindings'].items():
        raw = git('show', runtime['frozenPlatformCommit'] + ':' + name)
        assert row['commit'] == runtime['frozenPlatformCommit']
        assert len(raw) == row['bytes'] and SHA(raw) == row['sha256']
        assert bound(runtime_home / 'platform-source' / name, row) == raw
    assert not runtime['originalRetailFilesLinked'] and not runtime['originalAssetsCopied']
    assert len(runtime['generatedResourceAliases']) == 28
    aliased_bytes = 0
    for row in runtime['generatedResourceAliases']:
        assert row['source'].startswith('runtimes/th14/th14_web/assets/sdl-native/')
        original, alias = ROOT / row['source'], runtime_home / row['path']
        assert os.path.samefile(original, alias)
        bound(original, row)
        aliased_bytes += row['bytes']
    assert aliased_bytes == runtime['generatedResourceBytesAliased']
    assert launcher['runtimeReportSha256'] == SHA(read(ROOT / launcher['runtimeReport']))
    assert transport['reportSha256'] == SHA(read(launcher_path))
    assert transport['routes'] == len(launcher['files']) == 139
    assert transport['quietByDefault'] and not transport['payloadFilesCopied']
    for name, row in launcher['files'].items():
        bound(ROOT / row['path'], row)
    for name, digest in transport['sourceBindings'].items():
        assert SHA(read(ROOT / name)) == digest
    assert len(transport['requests']) == 27
    assert transport['contractChecks'] == ['validateHostManifest', 'validateReleaseCatalog', 'validatePackageDescriptor']
    assert {row['status'] for row in transport['requests']} == {200, 404, 405}
    assert any(row['path'].endswith('th14-sdl.wasm') and row['status'] == 200 for row in transport['requests'])
    assert any(row['path'] == '/app-shell-sw.js' and row['localPassthrough'] for row in transport['requests'])
    assert not launcher['payloadFilesCopied'] and not launcher['defaultPreviewChanged']
    assert not runtime['defaultPreviewChanged']
    return dict(schema='th14/frozen-delivery-evidence/1', verifiedFrozenDelivery=True,
        publishedCoreCommit=CORE, platformCommit=runtime['frozenPlatformCommit'],
        wasmSha256=browser['wasmSha256'], compiledBrowserUnits=146,
        coreSourceAndHeaderBindings=len(core_bindings), frozenPlatformFiles=8,
        generatedAliases=28, generatedBytesAliased=aliased_bytes,
        routeCount=139, httpChecks=27, quietByDefault=True,
        routeMetadataBytesWritten=launcher['physicalBytesWritten'],
        defaultPreviewChanged=False, browserRun=False, browserAcceptance=False,
        persistenceAccepted=False, completeGame=False, nativeEquivalent=False,
        scope='Frozen platform Git blobs and packaged source/resource hashes plus retained real loopback HTTP results. No browser UI, GPU presentation, audio device, storage, offline or whole-game acceptance.',
        bindings=bindings, verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = evidence()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT)
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        assert not output.exists()
        output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({key: result[key] for key in ['verifiedFrozenDelivery', 'routeCount', 'httpChecks', 'browserAcceptance']}))


if __name__ == '__main__':
    main()
