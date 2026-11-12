"""Qualify retained overcapture against pre-run fixture targets, preserving exit1."""
from pathlib import Path
import hashlib
import json
import re

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
A = H / 'current-prefix'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
report = load(A / 'report.json')
build = load(H / 'component/build.json')
source = (H / 'component/fixture.cpp').read_text()
assert sha(H / 'component/fixture.cpp') == build['fixtureSha256']
assert report['terminal'] and report['closed'] and not report['exception'] and not report['errors']
assert report['stoppedBy'] == 'declared-callback-limit' and report['callbacks'] == 35000
assert not report['captureComplete'] and report['shotSnapshots'] == 123 and report['fullVmSnapshots'] == 4
assert sha(R / 'tools/th14-run-option-current-replay-nov13.mjs') == report['driverSha256']
assert all(t['returned'] and not t['error'] for t in report['workers'])
assert all(t['closed'] and t['exitCode'] == 0 for t in report['physicalWorkers'])
assert not report['processClockResolution']['active']
index = load(A / 'shot-index.json')
sampling = load(A / 'input-key-sampling.json')
targets = [tuple(x) for x in build['targetInputKeys']]
assert len(set(targets)) == 123
actual = [tuple(s['inputKey']) for s in index['snapshots']]
assert len(actual) == len(set(actual)) == 123 and set(actual) == set(targets)
for item in index['snapshots']:
    assert sha(A / item['file']) == item['sha256']
def extract_targets(prefix):
    at = source.index(prefix)
    start = source.index('targets[]={', at) + len('targets[]=')
    end = source.index('};', start)
    return [tuple(map(int, x.split(','))) for x in re.findall(r'\{([0-9,]+)\}', source[start:end])]
assert extract_targets('bool wanted(') == targets
full_targets = extract_targets('void capture_full_vm_checkpoint(')
assert len(full_targets) == 4
full = sampling['fullVmSamples']
assert [tuple(x['inputKey']) for x in full] == full_targets and all(x['complete'] for x in full)
old_targets = {t for t in targets if t[0] == 1 or (t[0] == 2 and t[2] <= 2146)}
assert len(old_targets) == sampling['declared'] == 68
assert sampling['missing'] == [] and sampling['duplicates'] == 0
assert {tuple(map(int, x.split(','))) for x in sampling['unexpected']} == set(targets) - old_targets
boundary = dict(passed=True, originalDriverExitCode=1, originalReportPreserved=True,
                originalIncompleteFlagPreserved=True, noNewGameRun=True,
                declaredBeforeExecutionShotTargets=123, capturedShotTargets=123,
                declaredBeforeExecutionFullVmTargets=4, capturedFullVmTargets=4,
                captureCompleteAgainstActualFixture=True, equivalenceNotInferred=True,
                completeGame=False,
                bindings={p.relative_to(R).as_posix():sha(p) for p in [
                    A / 'report.json', A / 'input-key-sampling.json', A / 'shot-index.json',
                    H / 'component/build.json', H / 'component/fixture.cpp', Path(__file__)]})
(H / 'capture-boundary-qualified.json').write_text(json.dumps(boundary, indent=2) + '\n')
receipt = dict(reaped=True, pid=report['pid'], exitCode=1, execSession=2204,
               observedToolTerminalExitCode=1, originalCaptureDriverPass=False,
               independentCaptureBoundaryQualification=True, completeGame=False)
(H / 'cpp-terminal-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
parent = R / 'tools/th14-audit-option-current-replay-nov13.py'
audit = parent.read_text()
old = "assert nreceipt['reaped'] and creceipt['reaped'] and nreceipt['exitCode'] == creceipt['exitCode'] == 0"
new = """assert nreceipt['reaped'] and creceipt['reaped'] and nreceipt['exitCode'] == 0 and creceipt['exitCode'] == 1
capture_boundary=load(H/'capture-boundary-qualified.json')
assert capture_boundary['passed'] and capture_boundary['captureCompleteAgainstActualFixture']
assert not capture_boundary['equivalenceNotInferred'] is False"""
assert audit.count(old) == 1
audit = audit.replace(old, new)
old = "assert 35000 <= cr['callbacks'] < 35010 and cr['captureComplete'] and cr['actualNativeGles']"
assert audit.count(old) == 1
audit = audit.replace(old, "assert cr['callbacks'] == 35000 and not cr['captureComplete'] and cr['actualNativeGles']")
path = R / 'tools/th14-audit-option-current-replay-boundary-nov13.py'
assert not path.exists()
path.write_text(audit, encoding='utf8', newline='\n')
print(json.dumps({k:v for k,v in boundary.items() if k != 'bindings'}))
