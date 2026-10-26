"""Prepare an immutable local TH14 WebGPU Launcher route overlay.

The frozen Launcher and managed Runtime remain in their existing directories.
Only changed metadata is written: no original data, fonts, music or Wasm copies.
This tool neither starts nor drives a browser.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launcher-report', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parent_path = args.launcher_report.resolve(strict=True)
    runtime_home = args.runtime.resolve(strict=True)
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    assert runtime_home.is_relative_to(ROOT / 'artifacts/th14')
    parent_raw = parent_path.read_bytes()
    parent = json.loads(parent_raw)
    assert parent['passed'] and not parent['completeGame'] and not parent['nativeEquivalent']
    parent_site = Path(parent['site']).resolve(strict=True)
    assert parent_site.is_relative_to(ROOT / 'runtimes/th14/th14_web/artifacts')
    runtime_raw = (runtime_home / 'package-report.json').read_bytes()
    runtime = json.loads(runtime_raw)
    assert runtime['prepared'] and not runtime['browserRun'] and not runtime['browserAcceptance']
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('storage', ROOT / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    storage.check_budget(out)
    files = {}
    bindings = {}

    def name_ok(name):
        assert name and not name.startswith('/') and '\\' not in name
        assert '..' not in PurePosixPath(name).parts and str(PurePosixPath(name)) == name

    def reference(name, base, row):
        name_ok(name)
        path = (base / name).resolve(strict=True)
        assert path.is_relative_to(base) and path.is_file()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert digest == row['sha256'] and path.stat().st_size == row['bytes'], name
        return dict(path=path.relative_to(ROOT).as_posix(), bytes=row['bytes'], sha256=digest)

    def put(name, raw):
        name_ok(name)
        path = out / 'metadata' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        files[name] = dict(path=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256=SHA(raw))

    def read(name):
        path = ROOT / files[name]['path']
        raw = path.read_bytes()
        assert SHA(raw) == files[name]['sha256']
        return raw

    def put_json(name, value):
        put(name, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

    for name, row in parent['files'].items():
        if not name.startswith('runtime/') and name not in ['files.json', 'app-shell-sw.js']:
            files[name] = reference(name, parent_site, row)
    for name, row in runtime['files'].items():
        files['runtime/th14/' + name] = reference(name, runtime_home, row)
    raw = (runtime_home / 'runtime-files.json').read_bytes()
    files['runtime/th14/runtime-files.json'] = reference('runtime-files.json', runtime_home, dict(bytes=len(raw), sha256=SHA(raw)))
    descriptor = json.loads(read('packages/th14/package.json'))
    assert descriptor['game'] == 'th14' and len(descriptor['files']) == 1
    data = descriptor['files']['game-data']
    assert data['source'] == 'th14.data' and data['target'] == '/th14.data'
    archive = files['packages/th14/th14.data']
    assert data['bytes'] == archive['bytes'] and data['revision'] == 'sha256-' + archive['sha256']
    managed = json.loads(read('runtime/th14/manifest.json'))
    assert managed['game'] == 'th14' and managed['execution']['sha256'] == runtime['wasmSha256']
    host = json.loads(read('host-manifest.json'))
    assert set(host['games']) == {'th14'}
    game = host['games']['th14']
    assert game['runtime'] == './runtime/th14/th14.html'
    assert game['gameData']['sha256'] == archive['sha256'] and game['gameData']['bytes'] == archive['bytes']
    host['profile'] = 'th14-sdl3-webgpu-candidate'
    put_json('host-manifest.json', host)
    put_json('manifest.json', dict(game='th14', version='1.00b-webgpu-candidate', completeGame=False,
        nativeEquivalent=False, execution=dict(managed['execution'], bytes=files['runtime/th14/th14-sdl.wasm']['bytes'])))
    page = read('index.html').decode()
    assert 'data-game="th14"' in page and 'data-game="th11"' not in page
    page = page.replace('<title>', '<title>WebGPU 候选 · ', 1)
    put('index.html', page.encode())
    # App Shell excludes game data and original font/music resources.
    precache = [name for name in files if not name.startswith('packages/')
        and not name.startswith(('runtime/th14/fonts/', 'runtime/th14/music/'))]
    entries = [dict(url='./', revision=files['index.html']['sha256'])]
    entries += [dict(url=name, revision=files[name]['sha256']) for name in sorted(precache)]
    build_id = SHA(json.dumps(entries, separators=(',', ':')).encode())[:20]
    worker = ROOT / 'runtimes/th12/th12_web/launcher/src/app-shell-sw.js'
    worker_raw = worker.read_bytes()
    bindings[worker.relative_to(ROOT).as_posix()] = dict(bytes=len(worker_raw), sha256=SHA(worker_raw))
    source = worker_raw.decode()
    assert '__APP_SHELL_BUILD_ID__' in source and 'self.__WB_MANIFEST' in source
    put('app-shell-sw.js', source.replace('__APP_SHELL_BUILD_ID__', build_id)
        .replace('self.__WB_MANIFEST', json.dumps(entries, separators=(',', ':'))).encode())
    put_json('files.json', {name: row['sha256'] for name, row in sorted(files.items())})
    result = dict(schema='th14/webgpu-launcher-routes/1', prepared=True, candidateOnly=True,
        parentReport=parent_path.relative_to(ROOT).as_posix(), parentReportSha256=SHA(parent_raw),
        runtimeReport=(runtime_home / 'package-report.json').relative_to(ROOT).as_posix(), runtimeReportSha256=SHA(runtime_raw),
        roots=[parent_site.relative_to(ROOT).as_posix(), runtime_home.relative_to(ROOT).as_posix(), out.relative_to(ROOT).as_posix()],
        files=files, buildId=build_id, sourceBindings=bindings, wasmSha256=runtime['wasmSha256'],
        toolSha256=SHA(Path(__file__).read_bytes()), physicalBytesWritten=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
        existingPayloadBytesReferenced=sum(row['bytes'] for row in files.values() if not (ROOT / row['path']).is_relative_to(out)),
        originalFilesLinked=False, payloadFilesCopied=False, defaultPreviewChanged=False, frozenLauncherReused=True,
        browserRun=False, browserAcceptance=False, completeGame=False, nativeEquivalent=False,
        scope='Immutable route overlay of the frozen shared Launcher and current async-aware TH14 WebGPU candidate. Only metadata is written; existing data/resources/runtime are hash-checked and read in place. Packaging is not browser, offline, persistence or full-game acceptance.')
    (out / 'launcher-report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['prepared', 'wasmSha256', 'physicalBytesWritten', 'existingPayloadBytesReferenced', 'browserAcceptance']}))


if __name__ == '__main__':
    main()
