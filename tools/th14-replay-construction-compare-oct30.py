"""Compile production Replay restore and distinguish initial/stage contracts.

The GameSession call expression is read from source, not compiled as a whole
Application. Native decoding, GUI entry and full gameplay are separate gates.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--decoded', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--expect-legacy', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    raw = args.native.read_bytes()
    native = json.loads(raw)
    assert native['completed'] and native['caseCount'] == 576
    decoded = args.decoded.read_bytes()
    assert SHA(decoded) == native['decodedSha256']
    headers = {}
    offset = 0x94
    for _ in range(struct.unpack_from('<I', decoded, 0x78)[0]):
        stage = struct.unpack_from('<H', decoded, offset)[0]
        headers[stage] = decoded[offset:offset + 0xdc]
        offset += 0xdc + struct.unpack_from('<I', decoded, offset + 8)[0]
    assert offset == len(decoded)
    game = ROOT / 'runtimes/th12/th12_web/cpp/game'
    session_path = game / 'GameSession.cpp'
    session = session_path.read_text()
    old = 'entry.restore(economy,gameplay_rng,kPortTitle==14?state.demo:true,kPortTitle==14?&animations.script_rng:nullptr);'
    new = 'entry.restore(economy,gameplay_rng,true,kPortTitle==14?&animations.script_rng:nullptr);'
    assert session.count(old) + session.count(new) == 1
    legacy = old in session
    assert legacy == args.expect_legacy
    bindings = {}

    def bind(path):
        name = path.relative_to(ROOT).as_posix()
        if name in bindings:
            return
        data = path.read_bytes()
        bindings[name] = dict(bytes=len(data), sha256=SHA(data))
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"', data.decode(), re.M):
            include = next((f for f in (path.parent / name, game / name) if f.exists()), None)
            assert include, name
            bind(include.resolve())

    fixture = ROOT / 'runtimes/th12/th12_web/tests/cpp/th14-initial-replay-restore-fixture.cpp'
    for path in (fixture, game / 'Replay.cpp', session_path):
        bind(path)
    compiler = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    flags = ['--target=wasm32-wasip1', '-DPORT_TITLE=14', '-std=c++17', '-O2', '-g0',
             '-ffp-contract=off', '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti',
             '-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--export-memory', '-Wl,--allow-undefined', '-I' + str(game)]
    result = subprocess.run([str(compiler), *flags, str(fixture), str(game / 'Replay.cpp'), '-o', str(out / 'probe.wasm')],
                            capture_output=True, env={**os.environ, 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)})
    (out / 'compile.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    sys.path.insert(0, str(ROOT / 'tools/tmp/th14-native-gles-python/site'))
    import wasmtime as W
    engine = W.Engine()
    wasm = (out / 'probe.wasm').read_bytes()
    module = W.Module(engine, wasm)
    assert not list(module.imports)
    store = W.Store(engine)
    api = W.Instance(store, module, []).exports(store)
    api['_initialize'](store)
    memory = api['memory']
    pointer = api['probe_header'](store)
    selected = [2, 3, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    rows = []
    for case in native['cases']:
        header = headers[case['stage']]
        seed = struct.unpack_from('<H', header, 2)[0]
        assert seed == case['seed'] and SHA(header[0x14:0x84]) == case['globalsSha256']
        expected_rng = [(case['initialScriptSeed'] if case['initial'] else seed) | 0xa5a50000,
                        case['initialCalls'], seed | 0x5a5a0000, 0]
        assert expected_rng == case['rngWords']
        expected = expected_rng + [struct.unpack_from('<28I', header, 0x14)[i] for i in selected]
        memory.write(store, header, pointer)
        first = case['initial'] and not legacy
        result = api['probe_restore'](store, pointer, int(first), case['initialScriptSeed'], case['initialGameSeed'], case['initialCalls'])
        actual = list(struct.unpack('<26I', memory.read(store, result, result + 104)))
        rows.append(dict(initial=case['initial'], stage=case['stage'], actual=actual, expected=expected,
                         equal=actual == expected, differingWords=[i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]))
    initial = [r for r in rows if r['initial']]
    subsequent = [r for r in rows if not r['initial']]
    report = dict(schema='th14/replay-construction-comparison/1', caseCount=len(rows), rows=rows,
                  initialCases=len(initial), initialExactCases=sum(r['equal'] for r in initial),
                  existingStageCases=len(subsequent), existingStageExactCases=sum(r['equal'] for r in subsequent),
                  legacyInitialCallContract=legacy, actualRestoreBodyCompiled=True, wholeGameSessionCompiled=False,
                  initialGameSessionContractReadFromSource=True, nativeReportSha256=SHA(raw),
                  wasmSha256=SHA(wasm), compilerSha256=SHA(compiler.read_bytes()), sourceBindings=bindings,
                  flags=flags, toolSha256=SHA(Path(__file__).read_bytes()),
                  ordinaryMenuInitializationAccepted=False, completeGame=False, nativeEquivalent=False)
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'run-tool.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: v for k, v in report.items() if k not in ('rows', 'sourceBindings', 'flags')}), flush=True)
    assert all(r['equal'] for r in subsequent)
    if legacy:
        assert all(not r['equal'] and r['differingWords'] == [0] for r in initial)
    else:
        assert all(r['equal'] for r in initial)


if __name__ == '__main__':
    main()
