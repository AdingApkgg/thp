"""Publish only a derived historical summary; keep the dense source private.

No original receipt, publication tree/manifest, browser, Native or network edits.
Canonical array digests identify the untouched complete private failure records.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/porting/th14-staged-loader-integration-object-verified-oct14.json'
OUT = ROOT / 'docs/porting/th14-staged-loader-integration-object-public-summary-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()
CANON = lambda value: json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()


def main():
    assert not OUT.exists(), 'Completed public summary remains immutable'
    original = SOURCE.read_bytes()
    assert len(original) == 26998667
    assert SHA(original) == '4a95913494cb887e4027b0c4f8bc618ea431ef19e2de4d77d0a10e651b2766a0'
    full = json.loads(original)
    assert full['privatePrototype'] and not full['productionVerified']
    assert not full['completeGame'] and not full['nativeEquivalent'] and not full['passed']
    assert not full['gpuPrepared'] and not full['captureQueueIntegrated']
    assert full['comparedFrames'] == full['nativeCaptureCallbackCount'] == full['maximumCallbacks'] == 90793
    assert full['remainingNativeCallbacks'] == 0 and full['absentPlayerObservations'] == []
    assert full['physicalInvocationOrder'] and full['loadingCallbacksRetained']
    gameplay, detail, visual = full['differences'], full['detailDifferences'], full['startupVisualDifferences']
    assert (len(gameplay), len(detail), len(visual)) == (10, 65, 181570)
    detail_counts = Counter(row['kind'] for row in detail)
    assert detail_counts == {'enemyNextId': 57, 'damageAreas': 8}
    assert all(row['frame'] == 0 for row in detail if row['kind'] == 'enemyNextId')
    columns = Counter()
    for row in detail:
        if row['kind'] != 'damageAreas':
            continue
        port = {a[0]: a for a in row['port']}
        native = {a[0]: a for a in row['native']}
        assert port.keys() == native.keys() and len(port) == len(row['port']) and len(native) == len(row['native'])
        for slot in port:
            assert len(port[slot]) == len(native[slot]) == 20
            columns.update(i for i in range(20) if port[slot][i] != native[slot][i])
    assert columns == {8: 8}
    visual_fields = Counter(row['field'] for row in visual)
    assert visual_fields == {'scriptSeed': 90777, 'scriptCalls': 90793}
    assert len({row['index'] for row in visual}) == 90793

    def compact_detail(row):
        # Do not embed the complete original object arrays in public samples.
        sample = {key: row[key] for key in ('index', 'stage', 'frame', 'kind')}
        sample['portValueSha256'] = SHA(CANON(row['port']))
        sample['nativeValueSha256'] = SHA(CANON(row['native']))
        return sample

    arrays = {}
    for name, records in [('differences', gameplay), ('detailDifferences', detail), ('startupVisualDifferences', visual)]:
        transform = compact_detail if name == 'detailDifferences' else lambda row: row
        arrays[name] = dict(count=len(records), canonicalJsonSha256=SHA(CANON(records)),
                            first=[transform(records[0])], last=[transform(records[-1])],
                            fullArrayIncluded=False, fullArrayRetainedPrivately=True)
    engine = full['engineBuild']
    summary = dict(publicDerivedSummaryVerified=True, sourceOnly=True, historicalPrivatePrototype=True,
                   historicalRevision='private-controlled-v1', appliesToPrivateV3=False, appliesToCurrentProduction=False,
                   completeGame=False, nativeEquivalent=False, comparisonPassed=False,
                   originalFullEvidence=dict(path=SOURCE.relative_to(ROOT).as_posix(), bytes=len(original), sha256=SHA(original),
                                             privateOnly=True, includedInPublicSourceRelease=False),
                   comparedCallbacks=full['comparedFrames'], nativeCapturedCallbacks=full['nativeCaptureCallbackCount'],
                   requestedComparisonCallbackBudget=full['maximumCallbacks'], remainingNativeCallbacks=full['remainingNativeCallbacks'],
                   nativeOrdinaryTerminalVerified=False, historicalPrototypeTerminalPhase=full['terminalPhase'],
                   rawGameplayDifferences=len(gameplay), rawVisualDifferences=len(visual), retainedDetailDifferences=len(detail),
                   inactiveLoadingEnemyNextIdDifferences=detail_counts['enemyNextId'], activeDamageAreaDifferences=detail_counts['damageAreas'],
                   activeAreaChangedColumns=[8], activeAreaChangedColumnCounts=dict(columns),
                   gameplayDifferenceFields=dict(Counter(row['field'] for row in gameplay)), visualDifferenceFields=dict(visual_fields),
                   differenceArrays=arrays, canonicalArrayDigestEncoding='UTF-8 compact JSON, original array/object key order; ensure_ascii=false; no trailing newline.',
                   physicalInvocationOrder=full['physicalInvocationOrder'], inactiveLoadingCallbacksRetained=full['loadingCallbacksRetained'],
                   lateObservationWindow=full['lateObservationWindow'], absentPlayerObservationCount=len(full['absentPlayerObservations']),
                   clockMode=full['clockMode'], nativeCaseInitialization=full['nativeCaseInitialization'],
                   sourceReportedFlags={key: full[key] for key in ['privatePrototype', 'productionVerified', 'captureQueueIntegrated', 'gpuPrepared', 'passed']},
                   historicalPrivateSourceFiles=engine['sourceFilesVerified'], historicalPrivateSourceHashesSha256=SHA(CANON(engine['privateSourceHashes'])),
                   originalSourceReferences={key: full[key] for key in ['rawDetailPath', 'rawDetailSha256', 'portableStateSha256', 'nativeStateSha256', 'nativeTracePath',
                                                                       'nativeTraceSha256', 'archiveManifestSha256', 'replaySha256', 'wasmSha256', 'toolSha256']},
                   raw32BuffersIncluded=False, rawGpuBuffersIncluded=False, originalGameAssetsIncluded=False,
                   originalReportModified=False, publicationTreeModifiedByThisTool=False, networkRequests=0,
                   producerSha256=SHA(Path(__file__).read_bytes()),
                   scope='Derived metadata summary of the frozen private-controlled-v1 experiment only. All10 gameplay,181570 visual and65 object failures remain failed and their complete original arrays remain private, identified by exact source-file and canonical-array digests. Only one first and one last example per difference family is included; detail examples carry hashes rather than complete object arrays. No raw32/GPU buffer, original EXE/DAT/RPY/WASM/font/music or encoded asset payload is published by this summary. Private v3 and current267-source production evidence are separate; this historical run, declared60Hz clock and Native capture budget are not upgraded to current production, Native ordinary terminal, pixels/audio/storage or whole-game1:1. Publication exclusions and manifest/copy changes are handled separately by ROOT.')
    encoded = (json.dumps(summary, indent=2) + '\n').encode()
    assert len(encoded) < 20000
    assert SOURCE.read_bytes() == original, 'Frozen original changed'
    OUT.write_bytes(encoded)
    print(json.dumps(dict(summary=str(OUT), bytes=len(encoded), sha256=SHA(encoded), originalBytes=len(original), originalSha256=SHA(original), comparisonPassed=False, networkRequests=0)))


if __name__ == '__main__':
    main()
