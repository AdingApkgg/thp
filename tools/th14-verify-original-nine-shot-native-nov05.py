"""Recompute complete camera/cursor and actual RNG-access gates for one model."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(case):
    native = H / 'prefix-slots-v2/native'
    home = H / (case if case.startswith('overlap-') else 'comparison-'+case)
    model = home / 'model'
    output = home / 'expanded-verified.json'
    assert not output.exists()
    result = json.loads((home / 'result.json').read_bytes())
    assert result['strictDriverExitCode'] == result['rawVerifierExitCode'] == 0
    gate = json.loads((home / 'raw-verified.json').read_bytes())
    proof = json.loads((H / 'native-register-proof.json').read_bytes())
    assert proof['verifiedFiniteOriginalRegisterReadEvidence']
    count = proof['accessEvents']
    assert proof['decodedRegisterValues'] == count and count >= 64
    assert proof['arithmeticPairsEqual']*2 == count
    camera = (native / 'world-camera.raw').read_bytes()
    tail = (native / 'world-camera-tail.u32').read_bytes()
    actual = (model / 'full-camera.u32').read_bytes()
    assert len(camera) == 35000*292 and len(tail) == 35000*8 and len(actual) == 34999*300
    for i in range(1, 35000):
        assert actual[(i-1)*300:i*300] == camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]
    cursor = (native / 'replay-cursor.u32').read_bytes()
    actual = (model / 'replay-cursor.u32').read_bytes()
    assert len(cursor) == 35000*56 and len(actual) == 34999*16
    for i in range(1, 35000):
        assert struct.unpack_from('<4I', actual, (i-1)*16) == tuple(
            struct.unpack_from('<I', cursor, i*56+j*4)[0] for j in [3,7,8,9])
    accesses = [json.loads(line) for line in (native / 'script-rng-access-events.jsonl').read_bytes().splitlines()]
    portable = (model / 'rng-register-audit.u32').read_bytes()
    assert len(portable)%64 == 0 and len(accesses) == count
    # Keep every script-role row, in original output order. Never filter by
    # seed, counter, VM flags or identities to manufacture a matching sequence.
    rows = [row for row in struct.iter_unpack('<16I', portable) if row[3] == 0]
    assert len(rows) >= len(accesses)
    for event, row in zip(accesses, rows):
        kind = event['instructionContract']['kind']
        assert kind in ['mix32', 'store32']
        expected = [event['precedingPlayerCallbacks'], 1 if kind == 'mix32' else 4,
            event['valueRetainedByTrappedInstruction'],
            struct.unpack_from('<I', bytes.fromhex(event['rngHexAtObservation']), 4)[0]]
        assert [row[0], row[2], row[4], row[5]] == expected
    report = dict(verifiedExpandedFiniteComparison=True, case=case, callbacks=35000,
        all32StateFieldsEqual=True, comparedCameraWords=2624925,
        all75CameraWordsEqual=True, all4CursorFieldsEqual=True, all2HudFieldsEqual=True,
        actualOriginalInstructionAccesses=count, pairedNext32Calls=proof['arithmeticPairsEqual'],
        portableScriptRows=len(rows), extraPortableRowsNotAccepted=len(rows)-count,
        vm303Rows=gate['vm303Rows'], combatCheckpoints=gate['combatCheckpoints'],
        orderedPublications=gate['orderedPublications'],
        originalRngValuesProvidedToEngine=False, flagsUsedToFilter=False,
        nativeGlobalSnapshotMismatchCounts=proof['globalSnapshotMismatchCounts'],
        logicalOverlapDelivery=case.startswith('overlap-'), exactNativeScheduleAccepted=False,
        independentTimingAccepted=False, wholePixelsOrPcmCompared=False,
        completeGame=False, nativeEquivalent=False,
        rawVerifierSha256=SHA((home / 'raw-verified.json').read_bytes()),
        originalProofSha256=SHA((H / 'native-register-proof.json').read_bytes()),
        verifierSha256=SHA(Path(__file__).read_bytes()))
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['off', 'on', 'overlap-off', 'overlap-on'], required=True)
    main(parser.parse_args().case)
