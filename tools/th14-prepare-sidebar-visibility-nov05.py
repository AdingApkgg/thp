"""Build a TH14-only Launcher candidate using hidden instead of sidebar inert.

This is an ordinary UI compatibility candidate, without observer injection,
engine access, automatic dialogs, or reload recovery. It reuses all large
payloads by immutable, hash-checked route references. Browser acceptance must
be recorded separately; preparing this package does not prove the fix.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'artifacts/th14/raf-owned-swap-nov05/launcher/launcher-report.json'
PARENT_SHA = 'f2af706b48ba0a25fe1abfcc368fe433a65c7d2d53dd27c57dbe7fa32bbd027f'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    raw = PARENT.read_bytes()
    assert SHA(raw) == PARENT_SHA
    proof = json.loads(raw)
    assert proof['schema'] == 'th14/renderer-launcher-routes/1'
    assert proof['prepared'] and proof['candidateOnly'] and not proof['browserRun']
    assert proof['wasmSha256'] == '7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325'
    spec = importlib.util.spec_from_file_location('storage', ROOT / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    out.parent.mkdir(parents=True, exist_ok=True)
    storage.check_budget(out.parent)
    files = proof['files']
    for name, row in files.items():
        path = (ROOT / row['path']).resolve(strict=True)
        assert path.is_relative_to(ROOT) and path.is_file()
        assert path.stat().st_size == row['bytes'], name
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256'], name
    out.mkdir(parents=True)
    changes = {}

    def read(name):
        return (ROOT / files[name]['path']).read_bytes()

    def route(name, data):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        before = files.get(name)
        path.write_bytes(data)
        files[name] = dict(path=path.relative_to(ROOT).as_posix(), bytes=len(data), sha256=SHA(data))
        changes[name] = dict(before=before, after=files[name])

    # This frozen site contains TH14 only. Shared launcher sources and other
    # games are deliberately not rewritten by this focused candidate builder.
    html = read('index.html')
    assert b'data-game="th14"' in html and b'data-game="th11"' not in html
    old_html = b'<aside class="tools" aria-hidden="true">'
    assert html.count(old_html) == 1
    route('index.html', html.replace(old_html, b'<aside class="tools" aria-hidden="true" hidden>'))
    app_name = 'assets/launcher/app.mjs'
    app = read(app_name)
    old = b'    tools.inert = !state.hasSelection;'
    assert app.count(old) == 1
    new = (b'    // The inactive TH14 panel is absent from layout and focus traversal.\n'
           b'    // Avoid toggling inert on this subtree across iframe teardown.\n'
           b'    tools.hidden = !state.hasSelection;')
    route(app_name, app.replace(old, new))
    # Author display:flex overrides the browser's default [hidden] rule.
    css = read('styles.css')
    rule = b'\n/* TH14 sidebar availability follows the hidden attribute. */\n.tools[hidden]{display:none}\n'
    assert b'.tools[hidden]' not in css
    route('styles.css', css + rule)
    subprocess.run(['C:/nvm4w/nodejs/node.exe', '--check', str(out / app_name)],
                   check=True, capture_output=True, timeout=30)
    entries = [dict(url='./', revision=files['index.html']['sha256'])]
    entries += [dict(url=name, revision=row['sha256']) for name, row in sorted(files.items())
                if name not in ('files.json', 'app-shell-sw.js')
                and not name.startswith(('packages/', 'runtime/th14/fonts/', 'runtime/th14/music/'))]
    build_id = SHA(json.dumps(entries, separators=(',', ':')).encode())[:20]
    worker_path = ROOT / 'runtimes/th12/th12_web/launcher/src/app-shell-sw.js'
    worker = worker_path.read_bytes()
    assert b'__APP_SHELL_BUILD_ID__' in worker and b'self.__WB_MANIFEST' in worker
    route('app-shell-sw.js', worker.replace(b'__APP_SHELL_BUILD_ID__', build_id.encode())
          .replace(b'self.__WB_MANIFEST', json.dumps(entries, separators=(',', ':')).encode()))
    route('files.json', (json.dumps({name: row['sha256'] for name, row in sorted(files.items())
                                   if name != 'files.json'}, indent=2) + '\n').encode())
    unchanged = set(files) - set(changes)
    assert all(files[name] == json.loads(raw)['files'][name] for name in unchanged)
    assert all(not name.startswith(('runtime/', 'packages/')) for name in changes)
    proof['roots'].append(out.relative_to(ROOT).as_posix())
    proof.update(buildId=build_id, sidebarVisibilityCandidate=True,
                 parentReport=PARENT.relative_to(ROOT).as_posix(), parentReportSha256=SHA(raw),
                 toolSha256=SHA(Path(__file__).read_bytes()), changes=changes,
                 sourceBindings={worker_path.relative_to(ROOT).as_posix(): dict(bytes=len(worker), sha256=SHA(worker))},
                 physicalBytesWritten=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
                 payloadFilesCopied=False, frozenLauncherReused=True,
                 browserRun=False, browserAcceptance=False, nativeEquivalent=False, completeGame=False,
                 scope='TH14 sidebar hidden/display:none compatibility candidate. Three UI files plus derived metadata change; runtime and data routes remain byte-identical. Ordinary browser lifecycle acceptance is separate.')
    (out / 'launcher-report.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(prepared=True, buildId=build_id, changedRoutes=list(changes),
                          physicalBytesWritten=proof['physicalBytesWritten'],
                          wasmUnchanged=True, browserAcceptance=False, completeGame=False)))


if __name__ == '__main__':
    main()
