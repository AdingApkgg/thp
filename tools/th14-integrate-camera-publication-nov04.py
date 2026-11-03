"""Promote only the exact tested TH14 camera publication implementation."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/camera-publication-candidate-v3-nov04'
OLD = R / 'artifacts/th14/camera-publication-candidate-v2-nov04'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    assert sys.argv[1:] == ['--integrate']
    assert not (H / 'integration.json').exists()
    protected = {
        'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp': 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45',
        'artifacts/th14/vm-return-worker-oct29/work-state.json': '2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
    for name, digest in protected.items():
        assert sha((R / name).read_bytes()) == digest
    prepared = json.loads((H / 'prepared.json').read_bytes())
    prior_prepared = json.loads((OLD / 'prepared.json').read_bytes())
    for item in prepared['changes']:
        current = R / 'runtimes/th12' / item['path']
        assert sha(current.read_bytes()) == item['beforeSha256'], item['path']
        candidate = H / 'source' / item['path']
        assert sha(candidate.read_bytes()) == item['afterSha256']
        assert candidate.read_bytes().replace(b'\r\n', b'\n') == (OLD / 'source' / item['path']).read_bytes().replace(b'\r\n', b'\n')
    base = json.loads((OLD / 'core/observer-build.json').read_bytes())
    build = json.loads((H / 'core/observer-build.json').read_bytes())
    assert len(base['objectBindings']) == len(build['objectBindings']) == 141
    identical_objects = 0
    for before, after in zip(base['objectBindings'], build['objectBindings']):
        assert Path(before['path']).name == Path(after['path']).name
        assert sha(Path(before['path']).read_bytes()) == before['sha256']
        assert sha(Path(after['path']).read_bytes()) == after['sha256']
        identical_objects += int(before['sha256'] == after['sha256'])
    assert (H / 'core/observer.wasm').read_bytes() == (OLD / 'core/observer.wasm').read_bytes()
    assert build['wasmSha256'] == base['wasmSha256'] == sha((H / 'core/observer.wasm').read_bytes())
    for name in ('component.wasm', 'prior-component.wasm'):
        assert (H / 'core' / name).read_bytes() == (OLD / 'core' / name).read_bytes()
    native = (OLD / 'native-component.json').read_bytes()
    assert json.loads(native)['toolSha256'] == sha((R / 'tools/th14-camera-publication-native-nov04.py').read_bytes())
    (H / 'native-component.json').write_bytes(native)
    check = subprocess.run(['C:/nvm4w/nodejs/node.exe', str(R / 'tools/th14-camera-publication-check-nov04.mjs'), '--candidate', str(H)], capture_output=True, timeout=60)
    (H / 'component-check.log').write_bytes(check.stdout+check.stderr)
    assert check.returncode == 0, check.stderr.decode(errors='replace')
    regressions = json.loads((OLD / 'regressions/end.json').read_bytes())
    assert regressions['finitePasses'] == regressions['casesCompleted'] == 3 and regressions['callbacks'] == 199917
    syntax = json.loads((OLD / 'syntax/report.json').read_bytes())
    assert syntax['passed'] and len(syntax['cases']) == 12 and all(row['exitCode'] == 0 for row in syntax['cases'])
    for row in syntax['cases']:
        assert sha((OLD / 'source/th12_web/cpp/game' / row['source']).read_bytes()) == row['sourceSha256']
        assert (H / 'source/th12_web/cpp/game' / row['source']).read_bytes().replace(b'\r\n', b'\n') == (OLD / 'source/th12_web/cpp/game' / row['source']).read_bytes().replace(b'\r\n', b'\n')
    gate_home = H / 'revalidated-payloads'
    gate_home.mkdir()
    cases = json.loads((OLD / 'regressions/plan.json').read_bytes())['cases']
    for case in cases:
        directory = gate_home / case['key']
        directory.mkdir()
        command = [sys.executable, '-X', 'utf8', str(R / 'tools/th14-verify-native-campaign-exceptions-timing-v4-nov03.py'),
                   '--native', str(R / case['native']), '--model', str(OLD / 'regressions' / case['key'] / 'model'),
                   '--build', str(H / 'core/observer-build.json'),
                   '--exception-output', str(directory / 'exceptions.json'), '--timing-output', str(directory / 'timing.json'),
                   '--scene-output', str(directory / 'scene.json'), '--output', str(directory / 'raw-verified.json')]
        run = subprocess.run(command, capture_output=True, timeout=120)
        (directory / 'verified.log').write_bytes(run.stdout+run.stderr)
        assert run.returncode == 0, (case['key'], run.stderr.decode(errors='replace')[-2000:])
    # Every check above completes before any production gameplay source changes.
    for item in prepared['changes']:
        current = R / 'runtimes/th12' / item['path']
        assert sha(current.read_bytes()) == item['beforeSha256']
    for item in prepared['changes']:
        current = R / 'runtimes/th12' / item['path']
        current.write_bytes((H / 'source' / item['path']).read_bytes())
        assert sha(current.read_bytes()) == item['afterSha256']
    for name, digest in protected.items():
        assert sha((R / name).read_bytes()) == digest
    production = H / 'production-core'
    production.mkdir()
    (production / 'observer.wasm').write_bytes((H / 'core/observer.wasm').read_bytes())
    report = dict(build, isolatedPrototypeOnly=False, productionIntegrated=True, rootProductionSourcesModified=True,
                  productionSourceMatchVerified=True, sourcePublishedCommit=None,
                  parentGameplayCorePublishedCommit='5309e338232613bad6be96f1c2ad65090aaa74a2',
                  sourcePublicationPending=True, candidateChangedFiles=[item['path'] for item in prepared['changes']],
                  productionChangedGameFiles=[item['path'] for item in prepared['changes']],
                  candidateBuildReport=(H / 'core/observer-build.json').relative_to(R).as_posix(),
                  candidateBuildReportSha256=sha((H / 'core/observer-build.json').read_bytes()),
                  candidateWasmCopiedByteIdentically=True, all141GameObjectsByteIdenticalToCandidate=True)
    (production / 'observer-build.json').write_bytes((json.dumps(report, indent=2)+'\n').encode())
    receipt = dict(integrated=True, changedFiles=prepared['changes'], wasmSha256=build['wasmSha256'],
                   all141CoreObjectsRecompiled=True, bothObjectSetsIndividuallyHashBound=True,
                   byteIdenticalObjectContainersBetweenCandidates=identical_objects,
                   linkedObserverAndBothComponentWasmByteIdenticalBetweenCandidates=True,
                   finiteStrictPasses=3, finiteCallbacks=199917, controlledComponentCases=200,
                   priorCopiedRightDifferences=72, candidateCopiedRightDifferences=0,
                   otherTitleSyntaxChecks=12, sourcePublicationPending=True, protectedFiles=protected,
                   oldCameraOrRngFailuresClosed=False, copyWordInterleavingsImplemented=False,
                   completeGame=False, nativeEquivalent=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   integrationToolSha256=sha(Path(__file__).read_bytes()))
    (H / 'integration.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
