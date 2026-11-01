"""Reject corrupted native operands even after updating their container hash."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib
import json
from unittest.mock import patch

R = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()


def controls(home):
    home = home.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    verifier = importlib.import_module('th14-stage3-seed-write-evidence-nov02')
    positive = verifier.evidence(home)
    assert positive['verifiedFiniteNativeSeedWriteOperands']
    event_path = (home / 'native/script-seed-write-events.jsonl').resolve()
    report_path = (home / 'native/report.json').resolve()
    read_bytes = Path.read_bytes
    events_bytes = read_bytes(event_path)
    report_bytes = read_bytes(report_path)
    rows = [json.loads(line) for line in events_bytes.decode().splitlines()]

    def wrong_operand(events):
        events[0]['registers']['ecx'] ^= 1

    def disabled_hardware_watch(events):
        events[0]['debugControl'] &= ~(1 << 6)

    def changed_original_store(events):
        row = events[0]
        blob = bytearray.fromhex(row['originalCodeHex'])
        blob[row['pc'] - 1 - row['originalCodeStart']] ^= 1
        row['originalCodeHex'] = blob.hex()

    def erase_overwritten_memory_witness(events):
        row = next(x for x in events if x['isMainThread'] and
                   int.from_bytes(bytes.fromhex(x['rngHexAtObservation'])[:2], 'little') != x['registers']['ecx'] & 0xffff)
        blob = bytearray.fromhex(row['rngHexAtObservation'])
        blob[:2] = (row['registers']['ecx'] & 0xffff).to_bytes(2, 'little')
        row['rngHexAtObservation'] = blob.hex()

    def wrong_worker_store_operand(events):
        next(x for x in events if not x['isMainThread'])['registers']['eax'] ^= 1

    def remove_delivery_order_uncertainty(events):
        events[0]['crossThreadInstructionOrderNotAsserted'] = False

    negative = []
    for mutate in [wrong_operand, disabled_hardware_watch, changed_original_store,
                   erase_overwritten_memory_witness, wrong_worker_store_operand,
                   remove_delivery_order_uncertainty]:
        changed = copy.deepcopy(rows)
        mutate(changed)
        changed_bytes = ('\n'.join(json.dumps(row) for row in changed) + '\n').encode()
        report = json.loads(report_bytes)
        report['scriptSeedWriteEventsSha256'] = SHA(changed_bytes)
        replacement_report = json.dumps(report).encode()

        def simulated_read(path):
            resolved = path.resolve()
            if resolved == event_path:
                return changed_bytes
            if resolved == report_path:
                return replacement_report
            return read_bytes(path)

        rejected = False
        with patch.object(Path, 'read_bytes', simulated_read):
            try:
                verifier.evidence(home)
            except AssertionError:
                rejected = True
        assert rejected, mutate.__name__
        negative.append(dict(name=mutate.__name__, rejected=True,
                             containerHashResynchronized=True, actualFilesModified=False))
    assert read_bytes(event_path) == events_bytes and read_bytes(report_path) == report_bytes
    return dict(verifiedNativeOperandEvidenceControls=True, positiveCaseAccepted=True,
                corruptedCasesRejected=len(negative), cases=negative,
                nativeCaptureOrEngineFilesModified=False,
                verifierSha256=SHA((R / 'tools/th14-stage3-seed-write-evidence-nov02.py').read_bytes()),
                controlsSha256=SHA(Path(__file__).read_bytes()),
                completeGame=False, nativeEquivalent=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    result = controls(args.case)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))
