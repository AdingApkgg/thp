"""Run current finite replay evidence against the isolated camera candidate."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, subprocess, sys, time

R = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    home = args.candidate.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    component = json.loads((home / 'component-verified.json').read_bytes())
    assert component['verifiedControlledCameraPublicationComponent'] and component['priorCopiedRightDifferences'] == 72
    build = home / 'core/observer-build.json'
    digest = sha(build.read_bytes())
    assert json.loads(build.read_bytes())['isolatedPrototypeOnly']
    output = home / 'regressions'
    output.mkdir(exist_ok=False)
    cases = []
    for index in (1, 2):
        cases += json.loads((R / f'artifacts/th14/replay-cadence-reset-nov04/regressions/case-{index}/plan.json').read_bytes())['cases']
    cases.append(dict(key='sakuyaa-extra', native='artifacts/th14/replay-cadence-reset-nov04/sakuyaa-extra-full/native',
                      assets='artifacts/th14/native-campaign-assets/57d84a5cbe82-c93a499bfa14', selection=[2, 0, 4, 7],
                      driver=str(R / 'tools/th14-compare-native-extra-campaign-nov01.mjs')))
    plan = dict(cases=cases, buildSha256=digest, noOriginalProcessesLaunched=True, physicalAudioDevicesOpened=0,
                maximumSecondsPerModel=240, maximumSecondsPerVerifier=240, maximumBytesPerCase=128*1024**2,
                minimumFreeBytes=100*1024**3, productionIntegrated=False, completeGame=False, nativeEquivalent=False)
    (output / 'plan.json').write_bytes((json.dumps(plan, indent=2)+'\n').encode())
    spec = importlib.util.spec_from_file_location('storage', R / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)

    def run(command, directory, label):
        start = time.monotonic()
        guard = None
        with (directory / (label+'.log')).open('wb') as stream:
            child = subprocess.Popen(command, cwd=R, stdout=stream, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            while child.poll() is None:
                try:
                    storage.check_budget(directory, plan['minimumFreeBytes'], plan['maximumBytesPerCase'])
                except RuntimeError:
                    guard = 'storage-budget'
                if time.monotonic()-start > 240:
                    guard = 'wall-budget'
                if guard:
                    child.terminate()
                    child.wait(timeout=30)
                    break
                time.sleep(1)
        receipt = dict(exitCode=child.returncode, guardStop=guard, elapsedSeconds=time.monotonic()-start)
        (directory / (label+'-end.json')).write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
        return receipt

    results = []
    for case in cases:
        assert sha(build.read_bytes()) == digest
        directory = output / case['key']
        directory.mkdir()
        storage.check_budget(directory, plan['minimumFreeBytes'], plan['maximumBytesPerCase'])
        native = R / case['native']
        report = json.loads((native / 'report.json').read_bytes())
        assert report['childExited'] and report['observedForcedReplayEndMenu'] and not report['error'] and not report['debugErrors']
        model = directory / 'model'
        command = ['C:/nvm4w/nodejs/node.exe', case['driver'], '--native', str(native), '--assets', str(R / case['assets']),
                   '--build', str(build), '--output', str(model), '--selection', ','.join(map(str, case['selection'])), '--scheduler-phases', 'observed']
        modeled = run(command, directory, 'model')
        verified = None
        if modeled['exitCode'] == 0 and modeled['guardStop'] is None:
            command = [sys.executable, '-X', 'utf8', str(R / 'tools/th14-verify-native-campaign-exceptions-timing-v4-nov03.py'),
                       '--native', str(native), '--model', str(model), '--build', str(build),
                       '--exception-output', str(directory / 'exceptions.json'), '--timing-output', str(directory / 'timing.json'),
                       '--scene-output', str(directory / 'scene.json'), '--output', str(directory / 'raw-verified.json')]
            verified = run(command, directory, 'verifier')
        passed = modeled['exitCode'] == 0 and modeled['guardStop'] is None and verified is not None and verified['exitCode'] == 0 and verified['guardStop'] is None
        row = dict(key=case['key'], callbacks=report['callbacks'], model=modeled, verifier=verified, strictAndIndependentPassed=passed)
        results.append(row)
        receipt = dict(results=results, casesCompleted=len(results), finitePasses=sum(item['strictAndIndependentPassed'] for item in results),
                       callbacks=sum(item['callbacks'] for item in results), buildSha256=digest,
                       productionIntegrated=False, completeGame=False, nativeEquivalent=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (output / 'progress.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
        print(json.dumps(row), flush=True)
        if not passed:
            (output / 'stopped.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
            raise SystemExit(1)
    (output / 'end.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())


if __name__ == '__main__':
    main()
