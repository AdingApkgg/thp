"""Link the actual-slot template oracle to the current normal game providers."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--providers', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    provider_path = a.providers.resolve() / 'build.json'
    provider = json.loads(provider_path.read_bytes())
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    assert provider['normalEngineAccessControl']
    for name, digest in provider['sourceBindings'].items():
        assert sha(ROOT / name) == digest, name
    for row in provider['currentProviders']:
        assert sha(ROOT / row['object']) == row['objectSha256']
    parent = ROOT / 'runtimes/th12/th12_web/tests/cpp/th14-anm-all-resource-loader-fixture.cpp'
    expanded = ROOT / 'tools/th14-anm-template303-fixture-nov10.inc'
    source = parent.read_text().replace('../../cpp/game/AnmManager.hpp', 'AnmManager.hpp')
    source = source.replace('../../cpp/game/AnmOpcodes.hpp', 'AnmOpcodes.hpp')
    source = source.replace('API(open) u32 open(', 'API(resource_open_probe) u32 resource_open_probe(')
    source += '\n' + expanded.read_text()
    fixture = out / 'fixture.cpp'
    fixture.write_text(source, encoding='utf8', newline='\n')
    cc = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(cc) == provider['compilerSha256']
    command = [str(cc), *provider['flags'], '-mexec-model=reactor', '-Wl,--no-entry',
               '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
               '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
               '-Wl,-z,stack-size=1048576', str(fixture),
               *[row['object'] for row in provider['currentProviders']], '-o', str(out / 'loader.wasm')]
    assert '-fno-access-control' not in command
    with (out / 'build.log').open('wb') as stream:
        subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                       env=dict(os.environ, TEMP=str(out), TMP=str(out), TMPDIR=str(out)),
                       check=True, timeout=120)
    report = dict(sourceBindings=provider['sourceBindings'],
                  objectBindings={row['object']: row['objectSha256'] for row in provider['currentProviders']},
                  fixtureSha256=sha(fixture), wasmSha256=sha(out / 'loader.wasm'),
                  toolSha256=sha(Path(__file__)), command=command,
                  providerBuild=str(provider_path), providerBuildSha256=sha(provider_path),
                  parentFixtureSha256=sha(parent), expandedObserverSha256=sha(expanded),
                  normalAccessControl=True, gameObjectsReused=len(provider['currentProviders']),
                  engineUnitsChanged=0, completeGame=False)
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'wasmSha256': report['wasmSha256'], 'normalAccessControl': True}))


if __name__ == '__main__':
    main()
