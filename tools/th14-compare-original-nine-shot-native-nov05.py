"""Compare the new A-profile native shot capture with unchanged strict gates."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def prepare():
    parent = R / 'artifacts/th14/original-nine-shot-model-nov05/retry1/on/driver.mjs'
    raw = parent.read_bytes()
    assert SHA(raw) == '73f039735603aa2b324833e53f7a20e1c43fbce3e2e734bbe31c5bcd3a8c1fcd'
    source = raw.decode()
    before = "'tools/th14-player-pump-trace-evidence-nov05.py'"
    after = "'tools/th14-original-nine-shot-read-evidence-nov05.py'"
    assert source.count(before) == 1
    source = source.replace(before, after)
    assert source.replace(after, before).encode() == raw
    off = source.replace('c.shot_lifetime_install(1)', 'c.shot_lifetime_install(0)')
    assert off != source and off.replace('c.shot_lifetime_install(0)', 'c.shot_lifetime_install(1)') == source
    home = H / 'comparison-driver'
    assert not home.exists()
    home.mkdir()
    for name, text in [('driver.mjs', source), ('driver-off.mjs', off)]:
        (home / name).write_text(text, encoding='utf8', newline='\n')
        subprocess.run(['C:/nvm4w/nodejs/node.exe', '--check', str(home / name)],
                       check=True, capture_output=True, timeout=30)
    result = dict(prepared=True, parentDriverSha256=SHA(raw),
        driverSha256=SHA((home / 'driver.mjs').read_bytes()),
        offDriverSha256=SHA((home / 'driver-off.mjs').read_bytes()),
        onlyObserverProvenanceChanged=True, allOriginalComparisonsAndGatesPreserved=True,
        originalValuesProvidedToEngine=False, completeGame=False,
        toolSha256=SHA(Path(__file__).read_bytes()))
    (home / 'prepared.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


def main(case):
    if case == 'prepare':
        prepare()
        return 0
    native = H / 'prefix-slots-v2/native'
    end = json.loads((native.parent / 'process-end.json').read_bytes())
    report = json.loads((native / 'report.json').read_bytes())
    assert end['exitCode'] == 1 and end['guardStop'] is None
    assert report['callbacks'] == 35000 and report['childExited']
    assert not report['error'] and not report['debugErrors']
    assert report['shotLifetimeReadOnly'] and report['configuredMusicAndSoundVolumeZero']
    prep = json.loads((H / 'comparison-driver/prepared.json').read_bytes())
    out = H / ('comparison-'+case)
    assert not out.exists()
    out.mkdir()
    proof = H / 'native-register-proof.json'
    if case == 'off':
        assert not proof.exists()
        subprocess.run([sys.executable, '-X', 'utf8',
            str(R / 'tools/th14-original-nine-shot-read-evidence-nov05.py'),
            '--native', str(native), '--output', str(proof)], cwd=R, check=True, timeout=60)
    else:
        prior = json.loads((H / 'comparison-off/result.json').read_bytes())
        assert prior['strictDriverExitCode'] == prior['rawVerifierExitCode'] == 0
    driver = H / 'comparison-driver' / ('driver-off.mjs' if case == 'off' else 'driver.mjs')
    assert SHA(driver.read_bytes()) == prep['offDriverSha256' if case == 'off' else 'driverSha256']
    build = R / 'artifacts/th14/shot-lifetime-nov05/build-retry1/observer-build.json'
    events = [json.loads(line) for line in (native / 'script-rng-access-events.jsonl').read_bytes().splitlines()]
    first = min(row['precedingPlayerCallbacks'] for row in events)
    last = max(row['precedingPlayerCallbacks'] for row in events)+1
    argv = ['C:/nvm4w/nodejs/node.exe', '--no-warnings', str(driver), '--native', str(native),
        '--assets', str(R / 'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),
        '--build', str(build), '--output', str(out / 'model'), '--prefix', '35000',
        '--selection', '0,1,1,1', '--scheduler-phases', 'observed',
        '--rng-audit-first', str(first), '--rng-audit-last', str(last),
        '--native-read-evidence', str(proof)]
    (out / 'plan.json').write_text(json.dumps(dict(argv=argv, driverSha256=SHA(driver.read_bytes()),
        allOriginalComparisonsAndGatesPreserved=True, noOriginalValuesProvidedToEngine=True,
        diagnosticPrefixOnly=True, independentSchedulingAccepted=False, completeGame=False), indent=2)+'\n')
    started = time.monotonic()
    with (out / 'driver.log').open('wb') as log:
        child = subprocess.run(argv, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                               timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    raw_code = None
    if (out / 'model/report.json').exists():
        with (out / 'verify.log').open('wb') as log:
            verifier = subprocess.run([sys.executable, '-X', 'utf8',
                str(R / 'tools/th14-verify-native-campaign.py'), '--native', str(native),
                '--model', str(out / 'model'), '--build', str(build), '--prefix', '35000',
                '--output', str(out / 'raw-verified.json')], cwd=R,
                stdout=log, stderr=subprocess.STDOUT, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW)
        raw_code = verifier.returncode
    result = dict(case=case, strictDriverExitCode=child.returncode, rawVerifierExitCode=raw_code,
                  elapsedSeconds=time.monotonic()-started, completeGame=False)
    if case == 'on' and child.returncode == 0 and raw_code == 0:
        equal = []
        for name in ['selected-state.u32', 'full-camera.u32', 'replay-cursor.u32', 'portable-hud.u32']:
            data = (out / 'model' / name).read_bytes()
            assert data == (H / 'comparison-off/model' / name).read_bytes()
            equal.append(dict(file=name, bytes=len(data), sha256=SHA(data)))
        result['probeTransparentForCapturedState'] = equal
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 0 if child.returncode == 0 and raw_code == 0 else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['prepare', 'off', 'on'], required=True)
    raise SystemExit(main(parser.parse_args().case))
