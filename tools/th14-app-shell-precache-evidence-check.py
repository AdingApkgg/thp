"""Audit the frozen TH14 App Shell precache without changing its deployment.

Only this verifier's report is written. Optional loopback HTTP probes are GETs;
they do not install/unregister workers, change browser settings or mutate games.
Inventory violations and unknown warning causality remain explicit.
"""
import argparse
import hashlib
import http.client
import json
import re
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'docs/porting/th14-launcher-preview-prepared-hit-effects-oct14.json'
RUNTIME = ROOT / 'docs/porting/th14-launcher-runtime-prepared-hit-effects-oct14.json'
OUTPUT = ROOT / 'docs/porting/th14-app-shell-precache-verified-oct14.json'
NODE = Path('C:/nvm4w/nodejs/node.exe')
EXCLUDE_RULE = r'/^runtime\/[^/]+\/(?:music|fonts)\//.test(n)'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def bind(path):
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                sha256=sha(path))


def location(path, needle):
    lines = path.read_text(encoding='utf-8').splitlines()
    found = [i + 1 for i, line in enumerate(lines) if needle in line]
    assert len(found) == 1, needle
    return dict(path=path.relative_to(ROOT).as_posix(), line=found[0],
                text=lines[found[0] - 1], sha256=sha(path))


def probes(site, port, timeout):
    rows = []
    for host in ('127.0.0.1', 'localhost'):
        for name in ('app-shell-sw.js', 'site.webmanifest', 'files.json'):
            connection = http.client.HTTPConnection(host, port, timeout=timeout)
            start = time.monotonic()
            row = dict(url=f'http://{host}:{port}/{name}', method='GET',
                       proxyUsed=False, timeoutSeconds=timeout)
            try:
                headers = {'Cache-Control': 'no-cache'}
                if name == 'app-shell-sw.js':
                    headers['Service-Worker'] = 'script'
                connection.request('GET', '/' + name, headers=headers)
                response = connection.getresponse()
                body = response.read()
                row.update(status=response.status, headers=dict(response.getheaders()),
                           bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                           frozenFileBytesEqual=body == (site / name).read_bytes())
            except Exception as error:
                row.update(errorType=type(error).__name__, error=str(error),
                           winError=getattr(error, 'winerror', None))
            finally:
                connection.close()
                row['elapsedSeconds'] = round(time.monotonic() - start, 3)
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-http', action='store_true')
    parser.add_argument('--port', type=int, default=8207)
    parser.add_argument('--timeout', type=float, default=3)
    args = parser.parse_args()
    assert 1 <= args.port <= 65535 and 0 < args.timeout <= 5
    preview = json.loads(PREVIEW.read_text(encoding='utf-8'))
    runtime = json.loads(RUNTIME.read_text(encoding='utf-8'))
    assert preview['passed'] and runtime['passed']
    site = Path(preview['site']).resolve()
    runtime_dir = Path(runtime['out']).resolve()
    assert site.is_relative_to(ROOT / 'runtimes/th14/th14_web/artifacts/launcher-preview')
    assert runtime_dir.is_relative_to(ROOT / 'runtimes/th14/th14_web/artifacts/launcher-runtime')
    assert sha(ROOT / 'tools/th14-package-launcher.mjs') == preview['toolSha256']
    assert sha(ROOT / 'tools/th14-package-runtime.mjs') == runtime['toolSha256']
    assert sha(RUNTIME) == preview['runtimeManifestSha256']
    inventory = {}
    for name, expected in preview['files'].items():
        path = (site / name).resolve()
        assert path.is_relative_to(site) and path.stat().st_size == expected['bytes']
        assert sha(path) == expected['sha256'], name
        inventory[name] = dict(expected)
    assert len(inventory) == 127
    frozen = site / 'app-shell-sw.js'
    worker = frozen.read_text(encoding='utf-8')
    assert '__APP_SHELL_BUILD_ID__' not in worker and 'self.__WB_MANIFEST' not in worker
    assert 'importScripts(' not in worker
    syntax = subprocess.run([str(NODE), '--check', str(frozen)], capture_output=True,
                            text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    assert syntax.returncode == 0, syntax.stderr
    match = re.search(r'const PRECACHE_MANIFEST = (\[.*?\]);', worker, re.S)
    assert match
    manifest = json.loads(match.group(1))
    assert len(manifest) == 125
    entries = []
    groups, group_counts = Counter(), Counter()
    for entry in manifest:
        assert not urlparse(entry['url']).scheme and not entry['url'].startswith('/')
        name = 'index.html' if entry['url'] == './' else entry['url']
        assert name in inventory and entry['revision'] == inventory[name]['sha256']
        assert not name.startswith('packages/') and name not in ('files.json', 'app-shell-sw.js')
        group = ('originalGameFonts' if name.startswith('runtime/th14/fonts/') else
                 'originalGameMusic' if name.startswith('runtime/th14/music/') else 'shellAndRuntimeCode')
        if group != 'shellAndRuntimeCode':
            runtime_name = name.removeprefix('runtime/th14/')
            assert runtime_name in runtime['files']
            assert runtime['files'][runtime_name] == inventory[name]
            assert sha(runtime_dir / runtime_name) == inventory[name]['sha256']
        groups[group] += inventory[name]['bytes']
        group_counts[group] += 1
        entries.append(dict(url=entry['url'], file=name, category=group,
                            bytes=inventory[name]['bytes'], sha256=entry['revision']))
    total = sum(groups.values())
    assert dict(groups) == dict(shellAndRuntimeCode=4284044,
                               originalGameFonts=119577617, originalGameMusic=295272965)
    assert dict(group_counts) == dict(shellAndRuntimeCode=97, originalGameFonts=10, originalGameMusic=18)
    assert total == 419134626
    template = ROOT / 'runtimes/th12/th12_web/launcher/src/app-shell-sw.js'
    packager = ROOT / 'tools/th14-package-launcher.mjs'
    server = ROOT / 'tools/th14-serve-launcher.mjs'
    assert 'CACHE_RETENTION = 2' in worker and 'PRECACHE_CONCURRENCY = 3' in worker
    policy_locations = [location(template, '// App Shell only. Package/game content and Package DATA preparation are not'),
                        location(template, '// HTML/JS/WASM to this same precache so an installed game can start offline.'),
                        location(packager, "const precache=[...pendingFiles.keys()].filter"),
                        location(ROOT / 'tools/th14-package-runtime.mjs', 'original TH14 save/config/replay paths,10 fonts and18 lossless FLAC tracks.')]
    rule = lambda name: not re.match(r'^runtime/[^/]+/(?:music|fonts)/', name)
    proposed = [e for e in entries if rule(e['file'])]
    assert len(proposed) == 97 and sum(e['bytes'] for e in proposed) == 4284044
    http = probes(site, args.port, args.timeout) if args.probe_http else []
    result = dict(diagnosticOnly=True, evidencePassed=True, appShellPolicySatisfied=False,
                  currentWarningCauseEstablished=False, completeGame=False, nativeEquivalent=False,
                  productionChanged=False, packagerChanged=False, serviceWorkerChanged=False,
                  browserActionsTaken=False, browserConfigurationChanged=False,
                  deployment=preview['site'], buildId=preview['buildId'], verifiedSiteFiles=127,
                  generatedWorkerSyntaxPassed=True, noExternalWorkerImports=True,
                  allPrecacheRevisionsVerified=True, precacheEntries=125, precacheBytes=total,
                  categories={k: dict(entries=group_counts[k], bytes=v) for k, v in groups.items()},
                  gameAssetEntries=28, gameAssetBytes=414850582,
                  inventory=inventory, precacheInventory=entries, policyLocations=policy_locations,
                  cacheRetention=dict(versions=2, concurrentPrecacheRequests=3,
                                     twoFullVersionsBytes=total * 2,
                                     twoOldVersionsPlusInstallingThirdBytes=total * 3,
                                     scope='Derived potential cache storage demand only; actual browser quota, occupancy, eviction and install failure are not measured.'),
                  proposedRule=dict(javascriptExclusion=EXCLUDE_RULE,
                                    suggestedPrecacheFilter="n!=='files.json' && n!=='app-shell-sw.js' && !n.startsWith('packages/') && !/^runtime\\/[^/]+\\/(?:music|fonts)\\//.test(n)",
                                    retainedEntries=97, retainedBytes=4284044,
                                    excludesOriginalGameFontsAndMusic=True,
                                    preservesHostUiFontAssets=True,
                                    preservesRuntimeHtmlJsWasmAndDescriptorFiles=True,
                                    noGameAssetFilesDeleted=True),
                  proposedDocumentation='启动器外壳与运行时代码可以由 App Shell 缓存。游戏 DATA、原版字体和音乐不属于外壳预缓存；当前字体和音乐仍需联网读取，完整游戏离线运行尚未验证。',
                  httpProbes=http, httpResponseObtained=any('status' in row for row in http),
                  serverSourceFacts=dict(boundAddress='127.0.0.1',
                                         serviceWorkerMime='text/javascript; charset=utf-8',
                                         workerAtScopeRoot=True, serviceWorkerAllowedHeaderRequired=False,
                                         cacheControl='no-store', coop='same-origin', coep='require-corp', corp='same-origin',
                                         webmanifestDefaultMime='application/octet-stream',
                                         scope='Verified server source declarations; they are not observed response headers unless an HTTP probe succeeded.'),
                  findings=[
                      'Current packaging excludes packages/ but places all runtime music and game font binaries in the App Shell manifest: 28 original-game payload entries totaling 414850582 bytes.',
                      'This exceeds the stated App Shell policy scope. The proposed exclusion removes game font/music precache entries only, leaving their deployment files and ordinary network loading unchanged.',
                      'The 400MiB install and multi-version retention are actionable packaging/storage pressure. They do not prove that quota caused the retained unknown Service Worker fetch warning.',
                      'Generated worker syntax, all127 deployment file hashes, all125 precache revisions and same-origin relative paths are valid. No external worker import or unexpanded build placeholder was found.',
                      'Failed or unavailable HTTP probes cannot establish a browser platform limitation, a script MIME failure, a quota error or successful offline installation. Retain the warning until separately verified.'],
                  bindings=[bind(p) for p in (PREVIEW, RUNTIME, frozen, template, packager,
                                             ROOT / 'tools/th14-package-runtime.mjs', server)],
                  verifierSha256=sha(Path(__file__)),
                  scope='Read-only code, syntax and frozen-package inventory audit. This report establishes overbroad App Shell asset inclusion but keeps appShellPolicySatisfied:false and warning causality unknown. Optional proxy-free loopback GETs retain response/error facts. No worker installation, browser configuration change, quota modification, warning suppression, existing-packager edit, resource removal or whole-game/offline equivalence claim.')
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(evidencePassed=True, appShellPolicySatisfied=False,
                         warningCauseEstablished=False, precacheBytes=total,
                         proposedBytes=4284044, httpResponseObtained=result['httpResponseObtained'],
                         output=OUTPUT.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
