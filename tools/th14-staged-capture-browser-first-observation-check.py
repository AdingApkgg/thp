"""Bind ROOT's actual first browser observation, including its TDZ failure.

Read/hash/parse only: no browser control, server start, compiler or Native run.
The first package and whole console remain historical after a host-only fix.
"""
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/th14/browser-staged-capture-oct14'
DOC = ROOT / 'docs/porting/th14-staged-capture-browser-first-observed-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    assert not DOC.exists(), 'Completed first observation remains immutable'
    bindings = {}
    def bind(path, expected=None, size=None):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        assert path.is_relative_to(ROOT)
        key = path.relative_to(ROOT).as_posix()
        h = hashlib.sha256()
        with path.open('rb') as f:
            while chunk := f.read(4 * 1024 * 1024):
                h.update(chunk)
        row = dict(bytes=path.stat().st_size, sha256=h.hexdigest())
        if expected is not None:
            assert row['sha256'] == expected, key
        if size is not None:
            assert row['bytes'] == size, key
        bindings[key] = row
        return row
    def load(path):
        row = bind(path)
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        data = path.read_bytes()
        assert SHA(data) == row['sha256']
        return json.loads(data)
    def preserve_receipt(name, expected=None):
        source = ROOT / name
        binding = bind(source, expected)
        copy = ART / 'first-observed-custody' / source.name
        assert not copy.exists()
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(source.read_bytes())
        bind(copy, binding['sha256'], binding['bytes'])
        return json.loads(copy.read_bytes())

    console = load(ART / 'startup-all-console.json')
    ax_path, image = ART / 'startup-ax.txt', ART / 'startup.jpg'
    bind(ax_path); bind(image)
    ax = ax_path.read_text(encoding='utf-8')
    assert 'localhost:8208/index.html?game=th14' in ax
    assert 'localhost:8208/runtime/th14/th14.html?hosted=1&managedData=1' in ax
    assert 'th14-workspace-quiet' in ax and '本机测试静音' in ax and 'image canvas' in ax
    assert len(console) == 120
    assert all(set(row) == {'level', 'message', 'timestamp', 'url'} for row in console)
    assert all(datetime.fromisoformat(row['timestamp']) <= datetime.fromisoformat(console[-1]['timestamp']) for row in console)
    levels = Counter(row['level'] for row in console)
    errors = [row for row in console if row['level'] == 'error']
    warnings = [row for row in console if row['level'] in ('warn', 'warning')]
    assert len(errors) == 1 and errors[0]['timestamp'] == '2026-10-14T10:38:43.373Z'
    assert "ReferenceError: Cannot access 'state' before initialization" in errors[0]['message']
    assert 'renderServerStatusNote' in errors[0]['message'] and 'app.mjs:402:9' in errors[0]['message']
    assert 'app-shell-client.mjs:18:26' in errors[0]['message']
    def event(message, timestamp):
        rows = [row for row in console if row['message'] == message and row['timestamp'] == timestamp]
        assert len(rows) == 1
        row = rows[0]
        assert row['level'] == 'log' and row['url'] == 'http://localhost:8208/runtime/th14/th14-sdl.mjs'
        return row
    boot_start = event('[loading14] ascii script17 started; 9 resource uploads pending', '2026-10-14T10:39:37.650Z')
    boot_end = event('[loading14] resource uploads complete; interrupt1 delivered', '2026-10-14T10:39:38.393Z')
    demo_list = event('[demo] list entry 0 of 3: demo0.rpy', '2026-10-14T10:40:08.283Z')
    demo_load = event('[demo] loaded demo0.rpy, 7255 bytes', '2026-10-14T10:40:08.283Z')
    demo_record = event('[replay] demo: record stage 3, character 0 subtype 0 difficulty 1, 7255 bytes', '2026-10-14T10:40:08.283Z')
    demo_start = event('[loading14] stage entry; 5 resource uploads pending', '2026-10-14T10:40:08.334Z')
    demo_end = event('[loading14] resource uploads complete; interrupt1 delivered', '2026-10-14T10:40:08.398Z')
    after = [row for row in console if row['timestamp'] >= boot_start['timestamp']]
    historical = [row for row in console if row['timestamp'] < boot_start['timestamp']]
    assert all(row['level'] != 'error' for row in after)
    assert errors[0] in historical and len(after) + len(historical) == len(console)

    server = preserve_receipt('docs/porting/th14-local-workspace-current-staged-capture-server-verified-oct14.json')
    assert server['readOnlyVerified'] and not server['browserExecuted'] and not server['serverStarted']
    assert server['report'] == 'th14-launcher-preview-prepared-staged-capture-oct14.json'
    bind('tools/th14-serve-workspace-current.mjs', server['toolSha256'])
    assert server['toolSha256'] == '36accd68398804cb03803d2bc28d4f01d4d199633bba1536e32b6c33a5f07293'
    for filename, expected in server['frozenSources'].items():
        bind('tools/' + filename, expected)
    package = preserve_receipt('docs/porting/' + server['report'], server['reportSha256'])
    runtime = preserve_receipt('docs/porting/th14-launcher-runtime-prepared-staged-capture-oct14.json')
    assert package['passed'] and runtime['passed'] and not package['completeGame'] and not runtime['completeGame']
    assert len(package['files']) == 127 and len(runtime['files']) == 40
    site = Path(package['site'])
    runtime_path = Path(runtime['out'])
    for name, row in package['files'].items():
        bind(site / name, row['sha256'], row['bytes'])
    for name, row in runtime['files'].items():
        bind(runtime_path / name, row['sha256'], row['bytes'])
    sdl = runtime['build']
    assert (sdl['sha256'], sdl['bytes']) == ('64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54', 1890810)
    assert sdl['headers']['th12_web/cpp/sdl/ApplicationCaptureTh14.hpp'] == 'ef546985ec5786f78a869575cc1e70a41463cd8061ca645139cfe9c3bf1ffebd'
    bind(site / 'runtime/th14/th14-sdl.wasm', sdl['sha256'], sdl['bytes'])
    bind(server['publishedSw']['path'], server['publishedSw']['sha256'], server['publishedSw']['bytes'])
    assert not server['localSw']['fetchListener'] and not server['localSw']['cacheDeletion'] and not server['localSw']['saveDeletion']
    host_script = site / 'assets/launcher/app.mjs'
    lines = host_script.read_text(encoding='utf-8').splitlines()
    # Bind the exact first observed packaged host, not the concurrently edited
    # mutable launcher source or the following host-only repackage.
    host_source = dict(path=str(host_script), sha256=bind(host_script)['sha256'], errorReportedLine402=lines[401])

    report = dict(firstActualBrowserObservationEvidenceVerified=True, historicalFirstObserved=True,
                  completeGame=False, nativeEquivalent=False, productionChanged=False,
                  wholeObservationPassedWithoutErrors=False, wholeObservationConsoleRows=len(console),
                  wholeObservationConsoleLevels=dict(levels), wholeObservationConsoleErrorCount=len(errors),
                  wholeObservationConsoleWarningCount=len(warnings), retainedErrorRecords=errors, retainedWarningRecords=warnings,
                  allConsoleRecords=console, historicalConsoleRows=len(historical), runtimeWindowConsoleRows=len(after),
                  runtimeWindowStart=boot_start['timestamp'], runtimeWindowLast=after[-1]['timestamp'],
                  runtimeWindowErrorCount=sum(row['level'] == 'error' for row in after),
                  runtimeWindowWarningCount=sum(row['level'] in ('warn', 'warning') for row in after),
                  runtimeBootObservation=dict(pendingUploads=9, start=boot_start, completion=boot_end),
                  attractDemoObservation=dict(file='demo0.rpy', bytes=7255, stage=3, character=0, subtype=0, difficulty=1,
                                              pendingUploads=5, list=demo_list, load=demo_load, record=demo_record, start=demo_start, completion=demo_end),
                  canvasAndRuntimeChildObserved=True, quietBadgeObserved=True, speakerOutputMeasured=False,
                  localOriginObserved='http://localhost:8208', localSwResponseAdapterBound=True,
                  serverBoundModuleSha256=sdl['sha256'], serverBoundModuleBytes=sdl['bytes'], serverBoundHelperSha256=sdl['headers']['th12_web/cpp/sdl/ApplicationCaptureTh14.hpp'],
                  browserFetchedModuleDigestDirectlyObserved=False, packagedHostSource=host_source,
                  packagedFileCount=127, runtimeFileCount=40,
                  fullNextStageFlowVerified=False, longGameplayRunVerified=False, nativeGpuOrFullGameFrameEqualityVerified=False,
                  indexedDbPersistenceVerified=False, finalModuleCompleteBrowserFlowVerified=False,
                  bindings=bindings, bindingCount=len(bindings), toolSha256=SHA(Path(__file__).read_bytes()),
                  scope='ROOT-provided actual CUA console, AX tree and screenshot only. Entire120-row console, earlier histories and the10:38:43.373 host const-state TDZ failure remain; a later boot with9 uploads and attract demo0 stage3 with5 uploads completed in the observed runtime window. Zero post-boot errors is not zero errors for the whole observation. Source association is to the exact current server-bound64b46 frozen package/module and local passthrough/quiet adapters; the browser did not independently hash its loaded module in these data. Local quiet badge is not an actual loudspeaker measurement or Native audio proof. This first package becomes historical during the independent host TDZ fix/repackage; no full ordinary NextStage, long game, Native GPU/frame equality, IndexedDB persistence, zero-error complete browser acceptance or whole-game1:1 is inferred. Existing core checkpoint/browserfalse stays unchanged.')
    DOC.write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps(dict(report=str(DOC), sha256=SHA(DOC.read_bytes()), consoleRows=len(console), wholeErrors=len(errors), runtimeWindowErrors=report['runtimeWindowErrorCount'], bindings=report['bindingCount'])))


if __name__ == '__main__':
    main()
