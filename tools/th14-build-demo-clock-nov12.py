"""Build actual GameSession demo-clock regression with verified game providers."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--providers', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--fixture', type=Path, default=ROOT / 'tools/th14-demo-clock-component-nov12.cpp')
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    parent = args.providers.resolve() / 'build.json'
    build = json.loads(parent.read_text())
    assert build['normalEngineAccessControl']
    for name, digest in build['sourceBindings'].items():
        assert sha(ROOT / name) == digest, name
    for row in build['currentProviders']:
        assert sha(Path(row['object'])) == row['objectSha256']
    cc = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(cc) == build['compilerSha256']
    fixture = args.fixture.resolve()
    assert fixture.is_relative_to(ROOT)
    bindings = dict(build['sourceBindings'])
    for entry in [fixture, ROOT / 'tools/th14-demo-clock-component-nov12.cpp']:
        bindings[entry.relative_to(ROOT).as_posix()] = sha(entry)
    command = [str(cc), *build['flags'], '-mexec-model=reactor', '-Wl,--no-entry',
               '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
               '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
               '-Wl,-z,stack-size=1048576', str(fixture),
               *[row['object'] for row in build['currentProviders']], '-o', str(out / 'probe.wasm')]
    with (out / 'build.log').open('wb') as log:
        subprocess.run(command, cwd=ROOT, env=dict(os.environ, TEMP=str(out), TMP=str(out), TMPDIR=str(out)),
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=240)
    report = dict(sourceBindings=bindings, currentProviders=build['currentProviders'],
                  flags=build['flags'], fixtureSha256=sha(fixture), fixturePath=fixture.relative_to(ROOT).as_posix(),
                  parentSha256=sha(parent), compilerSha256=sha(cc), wasmSha256=sha(out / 'probe.wasm'),
                  fixtureNormalAccessControl=True, gameObjectsReused=len(build['currentProviders']), command=command,
                  completeGame=False, toolSha256=sha(Path(__file__)))
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    (out / 'fixture.cpp').write_bytes(fixture.read_bytes())
    print(json.dumps(dict(compiled=True, reused=report['gameObjectsReused'], wasmSha256=report['wasmSha256'])))


if __name__ == '__main__':
    main()
