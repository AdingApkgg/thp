"""Check changed shared C++ branches, including the WebGPU camera adapter."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
R = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(build, out):
    build, out = build.resolve(), out.resolve()
    assert build.is_relative_to(R / 'artifacts/th14') and out.is_relative_to(R / 'artifacts/th14') and not out.exists()
    raw = (build / 'build.json').read_bytes()
    metadata = json.loads(raw)
    assert metadata['sharedSceneCopyCandidate'] and metadata['compiledUnits'] == 146
    source = build / 'source'
    for name, info in metadata['sourceBindings'].items():
        assert SHA((source / name).read_bytes()) == info['sha256']
    out.mkdir(parents=True)
    sdk = R / 'runtimes/th12/tools/emsdk'
    env = {**os.environ, 'EM_CONFIG': str(sdk / '.emscripten'), 'EMSDK': str(sdk), 'EMSDK_PYTHON': sys.executable,
           'EMCC_CORES': '2', 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)}
    rows = []
    cases = [(title, False, 'game/' + name) for title in (12, 13, 14, 16)
             for name in ('GameSessionResources.cpp', 'GameBattle.cpp')]
    cases.append((14, True, 'sdl/Application.cpp'))
    for title, webgpu, name in cases:
        flags = [('-DPORT_TITLE=' + str(title)) if flag == '-DPORT_TITLE=14' else flag
                 for flag in metadata['flags'] if title == 14 or flag not in ['-pthread', '-DTH14_SHARED_SCENE_COPY=1']]
        if webgpu:
            flags += ['-DTH14_WEBGPU_BACKEND=1', '-DTH14_ARCHIVE_WORKER=1']
        label = f'{title}-' + name.replace('/', '_') + ('-webgpu' if webgpu else '')
        argv = [sys.executable, str(sdk / 'upstream/emscripten/emcc.py'), *flags, '-fsyntax-only', str(source / 'th12_web/cpp' / name)]
        (out / (label + '-argv.json')).write_text(json.dumps(argv, indent=2) + '\n')
        result = subprocess.run(argv, cwd=R, env=env, capture_output=True, timeout=120)
        (out / (label + '.log')).write_bytes(result.stdout + result.stderr)
        rows.append(dict(title=title, webgpu=webgpu, file=name, returncode=result.returncode))
        assert result.returncode == 0, f'Retain {label}.log'
    report = dict(cases=rows, syntaxOnly=True, sourceBuildSha256=SHA(raw), toolSha256=SHA(Path(__file__).read_bytes()),
                  otherTitleRuntimeAccepted=False, ordinaryBrowserAccepted=False, completeGame=False)
    (out / 'verified.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(syntaxCases=len(rows), completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.build, args.output)
