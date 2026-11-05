"""Recompile all141 game units for the actual shared-memory scene reader."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, os, shutil, subprocess

R = Path(__file__).resolve().parents[1]
B = R / 'artifacts/th14/independent-full-session-nov05/build'
SHA = lambda data: hashlib.sha256(data).hexdigest()
OVERLAYS = ['th12_web/cpp/game/GameBattle.cpp', 'th12_web/cpp/game/GameSessionResources.cpp',
            'th12_web/cpp/game/GameSessionResources.hpp', 'th12_web/cpp/game/SceneCameraReadJobTh14.hpp',
            'th12_web/cpp/sdl/Application.cpp', 'portable/sdl/Th14AsyncRuntime.mjs',
            'portable/sdl/Th14WebGpuRuntime.mjs', 'portable/sdl/Th14SharedSceneCopy.mjs',
            'portable/sdl/Th14SharedSceneWorker.mjs']


def main(out):
    out = out.resolve()
    assert out.is_relative_to(R / 'artifacts/th14') and not out.exists()
    assert shutil.disk_usage(R).free >= 100 * 1024**3
    base_raw = (B / 'build.json').read_bytes()
    base = json.loads(base_raw)
    assert base['wasmSha256'] == '081a74e2b777bb9c5cf316bf103b2e8f16e6f857a604f3cd2cec73aad6f634d0'
    inventory = dict(base['sourceBindings'])
    for name, row in inventory.items():
        assert SHA((B / 'source' / name).read_bytes()) == row['sha256'], name
    out.mkdir(parents=True)
    source, objects = out / 'source', out / 'objects'
    objects.mkdir()
    for path in (B / 'source').rglob('*'):
        if not path.is_file():
            continue
        name = path.relative_to(B / 'source').as_posix()
        if name in OVERLAYS:
            continue
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(path, target)
    for name in OVERLAYS:
        data = (R / 'runtimes/th12' / name).read_bytes()
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        inventory[name] = dict(bytes=len(data), sha256=SHA(data), origin='shared-scene-copy-candidate')
    fixture = R / 'runtimes/th12/th12_web/tests/cpp/th14-shared-scene-session-nov05.cpp'
    (out / 'fixture.cpp').write_bytes(fixture.read_bytes())
    compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert SHA(compiler.read_bytes()) == '945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
    flags = ['--target=wasm32-wasip1-threads', '-pthread', '-DPORT_TITLE=14', '-std=c++17', '-O2', '-g0',
             '-ffp-contract=off', '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti',
             *['-I' + str(source / name) for name in ['th12_web/cpp/game', 'th12_web/cpp/sdl', 'portable/sdl']]]
    link = ['-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory',
            '-Wl,--initial-memory=16777216', '-Wl,--max-memory=1073741824', '-Wl,-z,stack-size=1048576']
    units = sorted(base['objectHashes'])
    assert len(units) == 141
    env = {**os.environ, 'TEMP': str(objects), 'TMP': str(objects), 'TMPDIR': str(objects)}
    (out / 'build-tool.py').write_bytes(Path(__file__).read_bytes())

    def compile_unit(name):
        target = objects / (name.replace('/', '_') + '.o')
        argv = [str(compiler), *flags, '-MMD', '-MF', str(target) + '.d', '-c', str(source / name), '-o', str(target)]
        with (objects / (target.name + '.log')).open('wb') as log:
            result = subprocess.run(argv, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        assert result.returncode == 0, f'Retain {target.name}.log'
        return target

    compiled = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(compile_unit, name): name for name in units}
        for job in concurrent.futures.as_completed(jobs):
            compiled[jobs[job]] = job.result()
            assert shutil.disk_usage(R).free >= 100 * 1024**3
            (out / 'progress.json').write_text(json.dumps(dict(phase='compile', compiled=len(compiled), total=141)) + '\n')
            if len(compiled) % 16 == 0:
                print(f'compiled {len(compiled)}/141', flush=True)
    argv = [str(compiler), *flags, *link, str(out / 'fixture.cpp'), *[str(compiled[name]) for name in units], '-o', str(out / 'session.wasm')]
    (out / 'link-argv.json').write_text(json.dumps(argv, indent=2) + '\n')
    with (out / 'link.log').open('wb') as log:
        result = subprocess.run(argv, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode == 0, 'Retain link.log'
    for name in ['Th14SharedSceneCopy.mjs', 'Th14SharedSceneWorker.mjs']:
        (out / name).write_bytes((source / 'portable/sdl' / name).read_bytes())
    report = dict(compiled=True, gameUnitsRecompiled=141, oldObjectsReused=0, sharedWasmMemory=True,
                  sharedMemory=dict(initialPages=256, maximumPages=16384),
                  sourceSnapshotRoot=source.relative_to(R).as_posix(), sourceBindings=inventory, flags=flags, linkFlags=link,
                  objectHashes={name: SHA(compiled[name].read_bytes()) for name in units},
                  fixtureSha256=SHA((out / 'fixture.cpp').read_bytes()), wasmSha256=SHA((out / 'session.wasm').read_bytes()),
                  parentBuildSha256=SHA(base_raw), parentGlesBuildSha256=base['parentGlesBuildSha256'],
                  sharedSceneModuleFiles={name: dict(bytes=(out / name).stat().st_size, sha256=SHA((out / name).read_bytes()))
                                         for name in ['Th14SharedSceneCopy.mjs', 'Th14SharedSceneWorker.mjs']},
                  toolSha256=SHA(Path(__file__).read_bytes()), originalAssetsCopied=False,
                  ordinaryBrowserAccepted=False, nativeEquivalent=False, completeGame=False)
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'progress.json').write_text(json.dumps(dict(phase='compiled', compiled=141, total=141)) + '\n')
    print(json.dumps(dict(compiled=True, units=141, wasmSha256=report['wasmSha256'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
