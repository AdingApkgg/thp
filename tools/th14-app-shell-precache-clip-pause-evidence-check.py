"""Verify the corrected frozen App Shell cache and preserved game resources.

Requires explicit/current prepared preview and Runtime reports. It does not
rebuild SDL, mutate a browser, delete assets or certify complete offline play.
The previous overbroad-cache verifier/report remain immutable evidence.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_TOOL = ROOT / 'tools/th14-app-shell-precache-evidence-check.py'
OLD_REPORT = ROOT / 'docs/porting/th14-app-shell-precache-verified-oct14.json'
OUTPUT = ROOT / 'docs/porting/th14-app-shell-precache-clip-pause-verified-oct14.json'
NODE = Path('C:/nvm4w/nodejs/node.exe')
spec = importlib.util.spec_from_file_location('immutable_precache_helpers', OLD_TOOL)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
sha, bind, location = helper.sha, helper.bind, helper.location


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def report_path(name):
    assert re.fullmatch(r'[a-z0-9-]+\.json', name)
    return ROOT / 'docs/porting' / name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-report', default='th14-launcher-preview-prepared-clip-pause-oct14.json')
    parser.add_argument('--runtime-report', default='th14-launcher-runtime-prepared-clip-pause-oct14.json')
    parser.add_argument('--probe-http', action='store_true')
    parser.add_argument('--port', type=int, default=8207)
    parser.add_argument('--timeout', type=float, default=3)
    args = parser.parse_args()
    assert 1 <= args.port <= 65535 and 0 < args.timeout <= 5
    preview_path, runtime_path = report_path(args.preview_report), report_path(args.runtime_report)
    preview, runtime, old = read(preview_path), read(runtime_path), read(OLD_REPORT)
    assert sha(OLD_TOOL) == old['verifierSha256'], 'historical verifier changed'
    assert old['precacheBytes'] == 419134626 and not old['appShellPolicySatisfied']
    assert preview['passed'] and runtime['passed']
    assert sha(runtime_path) == preview['runtimeManifestSha256']
    assert sha(ROOT / 'tools/th14-package-launcher.mjs') == preview['toolSha256']
    assert sha(ROOT / 'tools/th14-package-runtime.mjs') == runtime['toolSha256']
    site, runtime_dir = Path(preview['site']).resolve(), Path(runtime['out']).resolve()
    assert site.is_relative_to(ROOT / 'runtimes/th14/th14_web/artifacts/launcher-preview')
    assert runtime_dir.is_relative_to(ROOT / 'runtimes/th14/th14_web/artifacts/launcher-runtime')
    current_sources = {}
    for group in ('sources', 'headers'):
        current_sources[group] = runtime['build'][group]
        for name, expected in current_sources[group].items():
            assert sha(ROOT / 'runtimes/th12' / name) == expected, 'stale SDL ' + name
    inventory = {}
    for name, expected in preview['files'].items():
        path = (site / name).resolve()
        assert path.is_relative_to(site)
        assert path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'], name
        inventory[name] = dict(expected)
    assert len(inventory) == 127
    for name, expected in runtime['files'].items():
        assert inventory['runtime/th14/' + name] == expected
        assert (runtime_dir / name).stat().st_size == expected['bytes']
        assert sha(runtime_dir / name) == expected['sha256']
    assert inventory['runtime/th14/th14-sdl.wasm']['sha256'] == runtime['build']['sha256']
    worker_path = site / 'app-shell-sw.js'
    worker = worker_path.read_text(encoding='utf-8')
    assert '__APP_SHELL_BUILD_ID__' not in worker and 'self.__WB_MANIFEST' not in worker
    assert 'importScripts(' not in worker
    syntax = subprocess.run([str(NODE), '--check', str(worker_path)], capture_output=True,
                            text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    assert syntax.returncode == 0, syntax.stderr
    match = re.search(r'const PRECACHE_MANIFEST = (\[.*?\]);', worker, re.S)
    assert match
    manifest = json.loads(match.group(1))
    assert len(manifest) == 97
    entries = []
    for entry in manifest:
        name = 'index.html' if entry['url'] == './' else entry['url']
        assert name in inventory and entry['revision'] == inventory[name]['sha256']
        assert not name.startswith('packages/') and name not in ('files.json', 'app-shell-sw.js')
        assert not re.match(r'^runtime/[^/]+/(?:music|fonts)/', name), name
        entries.append(dict(url=entry['url'], file=name, bytes=inventory[name]['bytes'],
                            sha256=entry['revision']))
    precache_bytes = sum(entry['bytes'] for entry in entries)
    assert precache_bytes < 5 * 1024 * 1024
    template_path = ROOT / 'runtimes/th12/th12_web/launcher/src/app-shell-sw.js'
    previous_template = next(item for item in old['bindings'] if item['path'] == template_path.relative_to(ROOT).as_posix())
    assert sha(template_path) == previous_template['sha256'], 'SW/security logic changed'
    template = template_path.read_text(encoding='utf-8')
    expected_worker = template.replace('__APP_SHELL_BUILD_ID__', preview['buildId']).replace(
        'self.__WB_MANIFEST', json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
    assert worker == expected_worker, 'worker differs beyond generated build/manifest'
    packager = ROOT / 'tools/th14-package-launcher.mjs'
    filter_source = location(packager, "const precache=[...pendingFiles.keys()].filter")
    assert r'!/^runtime\/[^/]+\/(?:music|fonts)\//.test(n)' in filter_source['text']
    previous_assets = {entry['file']: entry for entry in old['precacheInventory']
                       if entry['category'] in ('originalGameFonts', 'originalGameMusic')}
    assert len(previous_assets) == 28
    preserved = []
    for name, previous in previous_assets.items():
        assert inventory[name]['bytes'] == previous['bytes'] and inventory[name]['sha256'] == previous['sha256']
        assert not any(entry['file'] == name for entry in entries)
        preserved.append(dict(file=name, bytes=previous['bytes'], sha256=previous['sha256'],
                              preservedInSite=True, omittedFromAppShell=True))
    assert sum(row['bytes'] for row in preserved) == 414850582
    resource_manifest_path = runtime_dir / 'resources.json'
    resource_manifest = read(resource_manifest_path)
    assert len(resource_manifest['resources']) == 28
    for resource in resource_manifest['resources']:
        name = 'runtime/th14/' + resource['url'].removeprefix('./')
        assert name in previous_assets and resource['bytes'] == inventory[name]['bytes']
        assert resource['sha256'] == inventory[name]['sha256']
    for name, row in inventory.items():
        if name.startswith('packages/'):
            assert row == old['inventory'][name], 'managed game DATA changed'
    assert any(e['file'].startswith('assets/fonts/') for e in entries), 'Host UI fonts lost'
    for name in ('runtime/th14/th14.html', 'runtime/th14/th14-sdl.mjs',
                 'runtime/th14/th14-sdl.wasm', 'runtime/th14/resources.json'):
        assert any(e['file'] == name for e in entries), name
    http = helper.probes(site, args.port, args.timeout) if args.probe_http else []
    http_match = bool(http) and all(row.get('status') == 200 and row.get('frozenFileBytesEqual') for row in http)
    result = dict(diagnosticOnly=True, evidencePassed=True, appShellPolicySatisfied=True,
                  completeGame=False, nativeEquivalent=False, fullGameOfflineVerified=False,
                  currentWarningCauseEstablished=False, browserActionsTaken=False,
                  productionCppChangedByVerifier=False, browserConfigurationChanged=False,
                  deployment=preview['site'], runtimeBuildSha256=runtime['build']['sha256'],
                  buildId=preview['buildId'], verifiedSiteFiles=127,
                  currentSdlSourceFilesVerified=len(current_sources['sources']),
                  currentSdlHeadersVerified=len(current_sources['headers']), currentSdlSourceHashes=current_sources,
                  generatedWorkerSyntaxPassed=True, unchangedWorkerSecurityAndLifecycleTemplate=True,
                  actualPrecacheFilter=filter_source, precacheEntries=97, precacheBytes=precache_bytes,
                  previousPrecacheBytes=419134626, originalGameResourcesPreserved=28,
                  originalGameResourceBytesPreserved=414850582, managedDataPreserved=True,
                  runtimeHtmlJsWasmPreserved=True, hostUiFontAssetsPreserved=True,
                  preservedGameResources=preserved, inventory=inventory, precacheInventory=entries,
                  httpProbes=http, httpResponsesMatchFrozenPreview=http_match,
                  documentationScope='启动器外壳与运行时代码可以由 App Shell 缓存。游戏 DATA、原版字体和音乐不属于外壳预缓存；当前字体和音乐仍需联网读取，完整游戏离线运行尚未验证。',
                  bindings=[bind(path) for path in (preview_path, runtime_path, OLD_REPORT, OLD_TOOL,
                             worker_path, template_path, packager, resource_manifest_path,
                             ROOT / 'tools/th14-package-runtime.mjs')],
                  verifierSha256=sha(Path(__file__)),
                  scope='Independent current-source/frozen-package verification of the actual corrected App Shell manifest. All28 original font/music assets and managed DATA stay deployed with identical bytes; only shell caching inclusion changes. Worker lifecycle/security template stays byte-bound to the historical audit, and Runtime HTML/JS/WASM plus Host UI fonts stay precached. Optional proxy-free HTTP GETs retain response/error evidence. No browser install/offline test, quota change, warning suppression, original-game deletion or whole-game 1:1 claim.')
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(evidencePassed=True, appShellPolicySatisfied=True,
                         precacheEntries=97, precacheBytes=precache_bytes,
                         originalGameResourcesPreserved=28, httpResponsesMatchFrozenPreview=http_match,
                         output=OUTPUT.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
