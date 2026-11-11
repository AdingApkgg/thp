"""Build the Control/Overlay regression directly from current TH14 sources.

Only a WASI SDK is needed for compilation. Running the component additionally
needs the user's original th14.dat. No previous artifact/object chain is used.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, default=ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--jobs', type=int, choices=range(1, 9), default=3)
    args = parser.parse_args()
    compiler = args.sdk.resolve() / 'bin' / ('clang++.exe' if os.name == 'nt' else 'clang++')
    if not compiler.is_file():
        parser.error('A WASI SDK with wasm32-wasip1-threads support is required.')
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'objects').mkdir()
    game = ROOT / 'runtimes/th12/th12_web/cpp/game'
    fixture = ROOT / 'tools/th14-control-overlay-component-nov11.cpp'
    sources = sorted(game.glob('*.cpp'))
    tracked = {p for p in game.rglob('*') if p.is_file() and p.suffix in {'.cpp', '.hpp', '.h', '.inc'}}
    for directory in [game.parent, ROOT / 'runtimes/th12/portable']:
        tracked.update(p for p in directory.rglob('*') if p.is_file() and p.suffix in {'.hpp', '.h', '.inc'})
    application = game.parent / 'sdl/Application.cpp'
    app = application.read_text(encoding='utf8')
    test = fixture.read_text(encoding='utf8')

    def method(label):
        start = app.index(label)
        end, depth = app.index('{', start) + 1, 1
        while depth:
            depth += (app[end] == '{') - (app[end] == '}')
            end += 1
        return app[start:end]

    for label in ['    bool poll_cpp_initial_completion(', '    bool pump_cpp_initial_upload(']:
        if method(label) not in test:
            raise RuntimeError('Refresh the fixture from the current Application method: ' + label)
    start = app.index('            bool initial_stage_overlay_updated=false;')
    end = app.index('            if(signature_ready){', start)
    if app[start:end] not in test:
        raise RuntimeError('Refresh the fixture from the current initial-stage loading branch.')
    tracked.add(application)
    tracked.update([fixture, Path(__file__).resolve()])
    bindings = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(tracked)}
    flags = ['--target=wasm32-wasip1-threads', '-pthread', '-DPORT_TITLE=14',
             '-DTH14_CPP_BOOT_WORKER=1', '-DTH14_CPP_STAGE_WORKER=1',
             '-DTH14_CPP_STAGE_DECODE=1', '-DTH14_CPP_STAGE_RESOURCE_HANDSHAKE=1',
             '-DTH14_CPP_INITIAL_LOADING=1', '-DTH_NATIVE_PLATFORM=1',
             '-std=c++17', '-O2', '-g0', '-ffp-contract=off', '-fno-strict-aliasing',
             '-fno-exceptions', '-fno-rtti', '-I' + str(game)]
    link_flags = ['-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--import-memory',
                  '-Wl,--export-memory', '-Wl,--export-table', '-Wl,--allow-undefined',
                  '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
                  '-Wl,-z,stack-size=1048576']
    env = dict(os.environ, TMP=str(output), TEMP=str(output), TMPDIR=str(output))

    def run(command, log):
        with log.open('wb') as stream:
            subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                           check=True, timeout=240)

    def compile(source):
        obj = output / 'objects' / (source.name + '.o')
        run([str(compiler), *flags, '-c', str(source), '-o', str(obj)], obj.with_suffix('.log'))
        return dict(source=source.relative_to(ROOT).as_posix(), sourceSha256=sha(source),
                    object=str(obj), objectSha256=sha(obj))

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        providers = list(pool.map(compile, sources))
    commands = {}
    for mode in ['baseline', 'candidate']:
        command = [str(compiler), *flags, *link_flags]
        if mode == 'candidate':
            command.append('-DTH14_OVERLAY_TEST_CANDIDATE=1')
        command += [str(fixture), *[row['object'] for row in providers], '-o', str(output / (mode + '.wasm'))]
        commands[mode] = command
        run(command, output / (mode + '-link.log'))
    for name, digest in bindings.items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('Source changed during compilation: ' + name)
    report = dict(fixturePath=fixture.relative_to(ROOT).as_posix(), fixtureSha256=sha(fixture),
                  currentProviders=providers, sourceBindings=bindings, flags=flags, commands=commands,
                  outputs={mode: sha(output / (mode + '.wasm')) for mode in commands},
                  gameUnitsCompiled=len(providers), priorArtifactObjectsUsed=False,
                  normalEngineAccessControl=True, fixtureNormalAccessControl=True,
                  testedApplicationMethodsByteMatch=True, testedLoadingBranchByteMatches=True,
                  compilerSha256=sha(compiler), toolSha256=sha(Path(__file__)),
                  retailAssetsUsedAtBuildTime=False, completeGame=False)
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: report[key] for key in ['gameUnitsCompiled', 'priorArtifactObjectsUsed', 'outputs']}))


if __name__ == '__main__':
    main()
