"""Retain a full failed comparison privately and publish a bound compact receipt."""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('report', 'private', 'output'):
        p.add_argument('--'+name, required=True)
    args = p.parse_args()
    src, dst, out = [(ROOT/name).resolve() for name in (args.report, args.private, args.output)]
    assert src.is_relative_to(ROOT/'docs/porting') and out.is_relative_to(ROOT/'docs/porting')
    assert dst.is_relative_to(ROOT/'artifacts/th14/probe-failure-reports')
    assert not dst.exists() and not out.exists()
    data = src.read_bytes()
    report = json.loads(data)
    assert report['passed'] is False and not report['completeGame'] and not report['nativeEquivalent']
    result = {name: report[name] for name in ('passed', 'completeGame', 'nativeEquivalent',
        'physicalInvocationOrder', 'comparedFrames', 'nativeTracePath', 'nativeTraceSha256',
        'replaySha256', 'wasmSha256', 'engineBuild', 'toolSha256', 'scope') if name in report}
    for name, group in [('differences', 'field'), ('detailDifferences', 'kind'),
                        ('startupVisualDifferences', 'field'), ('absentPlayerObservations', None)]:
        rows = report.get(name, [])
        result[name+'Count'] = len(rows)
        result[name+'FirstRows'] = rows[:3]
        if group:
            result[name+'Kinds'] = dict(Counter(row[group] for row in rows))
    result.update(fullFailedReportRetained=True, privateReport=dict(
        path=dst.relative_to(ROOT).as_posix(), bytes=len(data), sha256=SHA(data)),
        receiptToolSha256=SHA(Path(__file__).read_bytes()),
        receiptScope='Compact publication only; all original differences, observations and provenance remain unchanged in the hash-bound private report. No failed comparison is converted to a pass.')
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    assert dst.read_bytes() == data
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=False, retainedBytes=len(data), receipt=str(out))))


if __name__ == '__main__':
    main()
