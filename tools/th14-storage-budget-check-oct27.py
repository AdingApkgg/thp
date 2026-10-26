"""Exercise storage scanning while compiler temporary files disappear."""
from pathlib import Path
from unittest.mock import patch
import argparse
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    source = ROOT / 'tools/th14-test-storage.py'
    spec = importlib.util.spec_from_file_location('storage', source)
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    retained = out / 'retained.bin'
    retained.write_bytes(b'12345678')
    # Equivalent to a compiler removing a file after os.walk has listed it.
    entries = [(str(out), [], ['retained.bin', 'compiler.o.tmp'])]
    with patch.object(storage.os, 'walk', return_value=entries):
        assert storage.check_budget(out, minimum_free=0, maximum_case=8) == 8
    with patch.object(storage.os, 'walk', return_value=entries):
        with patch.object(Path, 'lstat', side_effect=PermissionError('controlled unreadable entry')):
            try:
                storage.check_budget(out, minimum_free=0, maximum_case=8)
            except PermissionError:
                permission_rejected = True
            else:
                raise AssertionError('Permission errors must not be ignored')
    for minimum, maximum, gate in [(0, 7, 'case size'), (1 << 100, 8, 'free reserve')]:
        with patch.object(storage.os, 'walk', return_value=entries):
            try:
                storage.check_budget(out, minimum_free=minimum, maximum_case=maximum)
            except RuntimeError:
                limit = json.loads((out / 'storage-limit.json').read_bytes())
                assert limit['storageBudgetExceeded'] and limit['caseObservationBytes'] == 8
            else:
                raise AssertionError(gate + ' must reject')
    assert retained.read_bytes() == b'12345678'
    report = dict(passed=True, vanishedTemporaryEntryTolerated=True, retainedBytesCounted=8,
        permissionErrorRejected=permission_rejected, maximumCaseStillRejects=True,
        freeReserveStillRejects=True, retainedContentUnchanged=True,
        storageToolSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Controlled filesystem listing race plus non-missing error propagation and both budget gates. No original inputs or compiler state modified.')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
