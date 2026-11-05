"""Prepare/run the missing alternate-profile original shot/VM observation.

Reuses hash-frozen lifecycle, lookup, context and preflight gates. The original
player/pump watch profile stays intact; only bounded read-only snapshots and
the previously verified identical-context-write skip are added.
"""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(stage):
    if stage == 'prepare':
        path = R / 'tools/th14-prepare-shot-lifetime-native-nov05.py'
        expected = '6a5c57e3180557327bb6b02e427c44f0efd192aa533540052a478b03d1bc5b45'
        changes = [("H=R/'artifacts/th14/shot-lifetime-native-nov05'", "H=R/'artifacts/th14/original-nine-shot-native-nov05'", 1),
                   ("parent=R/'artifacts/th14/supervisor-pass-rng-nov05/observer-fixed-target/observer.py'",
                    "parent=R/'artifacts/th14/script-rng-read-generation-nov05/observer-player-pump/observer.py'", 1)]
    elif stage == 'context':
        path = R / 'tools/th14-context-noop-component-nov05.py'
        expected = '58d32eeb4fed761fd434f8efed0796554f0fce9285b9d9bf3520a47510ffbc7a'
        changes = [("H=R/'artifacts/th14/shot-lifetime-native-nov05'", "H=R/'artifacts/th14/original-nine-shot-native-nov05'", 1),
                   ('wanted=[0x44dbd0,0x444890,0x47d720,0]if main',
                    'wanted=[0x44dbd0,0x435b0f,0x456133,0]if main', 1)]
    elif stage == 'check':
        path = R / 'tools/th14-check-shot-lifetime-preflight-nov05.py'
        expected = '79afca7025a5c421c30e9f9a261770ba4f5bb852c9529a0578e9533d51b1a912'
        changes = [('artifacts/th14/shot-lifetime-native-nov05',
                    'artifacts/th14/original-nine-shot-native-nov05', 2)]
    else:
        context = json.loads((H / 'context-noop-component/report.json').read_bytes())
        prep = json.loads((H / 'observer-slots-v2/prepared.json').read_bytes())
        assert context['passed'] and context['fullInstallCases'] == 16
        assert context['sourceSha256'] == prep['observerSha256']
        lookup = json.loads((R / 'artifacts/th14/shot-lifetime-native-nov05/lookup-component.json').read_bytes())
        assert lookup['passed'] and lookup['componentCases'] == 29
        assert lookup['moduleSha256'] == prep['moduleSha256']
        if stage == 'prefix':
            assert json.loads((H / 'preflight-slots-v2/verified.json').read_bytes())['nativeShotSnapshotsVerified']
        path = R / 'tools/th14-run-player-pump-observer-nov05.py'
        expected = 'bbc8748f71754ba2226ece2ac68c723178f9f3a338621ab34afb0ed505906a15'
        changes = [("H=R/'artifacts/th14/script-rng-read-generation-nov05'", "H=R/'artifacts/th14/original-nine-shot-native-nov05'", 1),
                   ("choices=['player-pump'],default='player-pump'", "choices=['slots-v2'],default='slots-v2'", 1)]
    raw = path.read_bytes()
    assert SHA(raw) == expected
    source = raw.decode()
    for before, after, count in changes:
        assert source.count(before) == count, (before, source.count(before))
        source = source.replace(before, after)
    if stage in ['preflight', 'prefix']:
        import sys
        sys.argv = [str(Path(__file__)), '--case', stage]
    exec(compile(source, str(Path(__file__)), 'exec'),
         dict(__name__='__main__', __file__=str(Path(__file__).resolve())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['prepare', 'context', 'preflight', 'check', 'prefix'], required=True)
    main(parser.parse_args().stage)
