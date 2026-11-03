"""Compile the frozen draw-publication candidate and both controlled components."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, importlib.util, json, os, re, subprocess, time

R = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--resume-links', action='store_true', help='Reuse this failed build\'s unchanged141 compiled objects after its recorded fixture-include failure')
    args = parser.parse_args()
    home = args.candidate.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    prepared = json.loads((home / 'prepared.json').read_bytes())
    build_path = R / prepared['baseBuild']
    assert sha(build_path.read_bytes()) == prepared['baseBuildSha256']
    base = json.loads(build_path.read_bytes())
    source = Path(prepared['sourceRoot'])
    changes = {row['path']: row for row in prepared['changes']}
    for name, digest in {**base['sourceHashes'], **base['headerHashes']}.items():
        assert sha((source / name).read_bytes()) == changes.get(name, {}).get('afterSha256', digest), name
    out = home / 'core'
    assert out.exists() == args.resume_links
    if not out.exists():
        out.mkdir()
    spec = importlib.util.spec_from_file_location('storage', R / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    storage.check_budget(home, 100*1024**3, 128*1024**2)
    fixtures = home / 'fixtures'
    fixtures.mkdir(exist_ok=args.resume_links)
    fixture = fixtures / 'th14-native-campaign-fixture.cpp'
    original = Path(base['fixtureGraphRoot'])
    assert sha(original.read_bytes()) == base['expandedFixtureSha256']
    if args.resume_links:
        assert fixture.read_bytes() == original.read_bytes()
    else:
        fixture.write_bytes(original.read_bytes())
    component = fixtures / 'th14-camera-publication-fixture-nov04.cpp'
    component_raw = (R / 'runtimes/th12/th12_web/tests/cpp' / component.name).read_bytes()
    if args.resume_links:
        assert component.read_bytes() == component_raw
    else:
        component.write_bytes(component_raw)
    compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(compiler.read_bytes()) == base['compilerSha256']
    include = [source / 'th12_web/cpp' / part for part in ('game', 'sdl')]
    flags = [flag for flag in base['flags'] if not flag.startswith('-I')] + ['-I'+str(path) for path in include]
    env = dict(os.environ, TEMP=str(out), TMP=str(out))
    objects = out / 'objects'
    objects.mkdir(exist_ok=args.resume_links)
    started = time.monotonic()

    def compile_unit(name):
        path = source / name
        target = objects / (path.name+'.o')
        run = subprocess.run([str(compiler), *flags, '-c', str(path), '-o', str(target)], capture_output=True, env=env, timeout=180)
        (objects / (path.name+'.log')).write_bytes(run.stdout+run.stderr)
        assert run.returncode == 0, (name, run.stderr.decode(errors='replace')[-2000:])
        return dict(path=target.as_posix(), sha256=sha(target.read_bytes()))

    recovery = None
    if args.resume_links:
        failed = (out / 'observer.link.log').read_bytes()
        assert b"'th14-vm-return-worker-fixture.cpp' file not found" in failed
        recovery = dict(fixtureRelativeIncludeFailureSha256=sha(failed), objectsRecompiledAfterFailure=0,
                        unchangedPreparedSourcesVerified=True, includeSearchAddedOnlyToFixtureLinks=True)
        (out / 'first-fixture-include-failure.log').write_bytes(failed)
        rows = []
        for name in base['sourceHashes']:
            path = source / name
            target = objects / (path.name+'.o')
            assert target.exists() and (objects / (path.name+'.log')).exists()
            assert target.stat().st_mtime_ns >= path.stat().st_mtime_ns
            rows.append(dict(path=target.as_posix(), sha256=sha(target.read_bytes())))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(compile_unit, base['sourceHashes']))
    assert len(rows) == 141

    def link(target, unit, bindings, compile_flags):
        for row in bindings:
            assert sha(Path(row['path']).read_bytes()) == row['sha256']
        run = subprocess.run([str(compiler), *compile_flags, '-I'+str(original.parent), *base['linkFlags'], str(unit),
                              *[row['path'] for row in bindings], '-o', str(target)], capture_output=True, env=env, timeout=180)
        target.with_suffix('.link.log').write_bytes(run.stdout+run.stderr)
        assert run.returncode == 0, run.stderr.decode(errors='replace')[-2000:]

    link(out / 'observer.wasm', fixture, rows, flags)
    link(out / 'component.wasm', component, rows, flags+['-DTH14_CAMERA_PUBLICATION_HOOK=1'])
    prior_source = Path(base['sourceSnapshotRoot'])
    prior_flags = [flag for flag in base['flags'] if not flag.startswith('-I')] + ['-I'+str(prior_source / 'th12_web/cpp' / part) for part in ('game', 'sdl')]
    link(out / 'prior-component.wasm', component, base['objectBindings'], prior_flags)
    dependencies = {}

    def scan(path):
        path = path.resolve()
        if path.as_posix() in dependencies:
            return
        raw = path.read_bytes()
        dependencies[path.as_posix()] = sha(raw)
        for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"', raw.decode(), re.M):
            child = next((item for item in [path.parent / name, *[directory / name for directory in include], original.parent / name] if item.exists()), None)
            assert child, name
            scan(child)

    scan(fixture)
    report = dict(base, sourceHashes={name: sha((source / name).read_bytes()) for name in base['sourceHashes']},
                  headerHashes={name: sha((source / name).read_bytes()) for name in base['headerHashes']},
                  sourceSnapshotRoot=source.as_posix(), flags=flags, objectBindings=rows,
                  fixtureGraphRoot=fixture.as_posix(), expandedFixtureSha256=sha(fixture.read_bytes()),
                  fixtureDependencyHashes=dependencies, wasmSha256=sha((out / 'observer.wasm').read_bytes()),
                  parentBuildSha256=sha(build_path.read_bytes()), buildToolSha256=sha(Path(__file__).read_bytes()),
                  all141CoreObjectsRecompiled=True, rootProductionSourcesModified=False,
                  isolatedPrototypeOnly=True, productionIntegrated=False,
                  cameraPublicationBoundaryBeforePerspective=True,
                  cameraPublicationArbitraryClockSelected=False, oldCameraOrRngFailuresClosed=False,
                  fixtureIncludeSearchRecovery=recovery, fixtureExtraIncludeDirectory=original.parent.as_posix(),
                  completeGame=False, nativeEquivalent=False, elapsedSeconds=time.monotonic()-started)
    for key in ('productionSourceMatchVerified', 'promotedFromExactVerifiedCandidate', 'candidateWasmBytesReusedWithoutRelink'):
        report.pop(key, None)
    (out / 'observer-build.json').write_bytes((json.dumps(report, indent=2)+'\n').encode())
    components = dict(candidateSha256=sha((out / 'component.wasm').read_bytes()),
                      priorSha256=sha((out / 'prior-component.wasm').read_bytes()),
                      fixtureSha256=sha(component.read_bytes()), baseBuildSha256=sha(build_path.read_bytes()),
                      candidateObjects=141, priorObjectsReused=141, compilerSha256=sha(compiler.read_bytes()),
                      fullCoreBuildSha256=sha((out / 'observer-build.json').read_bytes()))
    (out / 'component-build.json').write_bytes((json.dumps(components, indent=2)+'\n').encode())
    storage.check_budget(home, 100*1024**3, 128*1024**2)
    print(json.dumps(dict(compiled=True, objects=len(rows), elapsedSeconds=report['elapsedSeconds'], wasmSha256=report['wasmSha256'])), flush=True)


if __name__ == '__main__':
    main()
