"""Compile the real SceneCamera/read-job asset-free shared-memory check."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess
R = Path(__file__).resolve().parents[1]
B = R / 'artifacts/th14/shared-scene-copy-nov05/session-build'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(out):
    out = out.resolve()
    assert out.is_relative_to(R / 'artifacts/th14') and not out.exists()
    raw = (B / 'build.json').read_bytes()
    build = json.loads(raw)
    assert build['sharedWasmMemory'] and build['gameUnitsRecompiled'] == 141
    for name, row in build['sourceBindings'].items():
        assert SHA((B / 'source' / name).read_bytes()) == row['sha256']
    out.mkdir(parents=True)
    fixture = R / 'runtimes/th12/th12_web/tests/cpp/th14-shared-scene-capture-nov05.cpp'
    (out / 'fixture.cpp').write_bytes(fixture.read_bytes())
    compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    argv = [str(compiler), *build['flags'], *build['linkFlags'], str(out / 'fixture.cpp'), '-o', str(out / 'component.wasm')]
    (out / 'argv.json').write_text(json.dumps(argv, indent=2) + '\n')
    env = {**os.environ, 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)}
    result = subprocess.run(argv, cwd=R, env=env, capture_output=True, timeout=90)
    (out / 'compile.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, 'Retain compile.log'
    metadata = dict(compiled=True, parentBuildSha256=SHA(raw), sharedMemory=build['sharedMemory'],
                    fixtureSha256=SHA((out / 'fixture.cpp').read_bytes()), wasmSha256=SHA((out / 'component.wasm').read_bytes()),
                    sourceBindings=build['sourceBindings'], sourceSnapshotRoot=build['sourceSnapshotRoot'],
                    toolSha256=SHA(Path(__file__).read_bytes()), originalAssetsUsed=False, gameSessionExecuted=False, completeGame=False)
    (out / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(dict(compiled=True, sharedMemory=True, completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
