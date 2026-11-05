"""Describe independent stage deliveries without exposing original RNG values.

The raw callback comparison remains authoritative; stage/frame pairing is only
a diagnostic. A live snapshot never accepts the replay or its scheduling.
"""
from pathlib import Path
import argparse, hashlib, json, struct

R = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(run, native, output, live):
    run, native, output = (p.resolve() for p in (run, native, output))
    assert all(p.is_relative_to(R / 'artifacts/th14') for p in (run, native, output))
    assert not output.exists()
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    plan = json.loads(raw(run / 'plan.json'))
    report = json.loads(raw(run / ('progress.json' if live else 'report.json')))
    original = json.loads(raw(native / 'report.json'))
    assert original['childExited'] and not original['error']
    assert original['sourceFullReplaySha256'] == plan['bindings']['replaySha256']
    assert SHA(raw(native / 'report.json')) == plan['bindings']['nativeReportSha256']
    expected = raw(native / 'selected-state.u32')
    assert SHA(expected) == original['selectedSha256']
    camera = raw(native / 'world-camera.raw')
    tail = raw(native / 'world-camera-tail.u32')
    hud = raw(native / 'hud-score.u32')
    data = raw(run / 'observations.u32')
    rows = min(report['callbacks'], len(data) // 456)
    compared = min(rows, original['callbacks'])
    first = None
    first_by_domain = {}
    windows = []
    stage_first = {}
    for index in range(compared):
        got = struct.unpack_from('<114I', data, index * 456)
        want = struct.unpack_from('<32I', expected, index * 128)
        wanted_camera = struct.unpack_from('<73I', camera, index * 292) + struct.unpack_from('<2I', tail, index * 8)
        wanted_hud = struct.unpack_from('<2I', hud, index * 8)
        differences = dict(selected=[i for i, (a, b) in enumerate(zip(got[1:33], want)) if a != b],
                           camera75=[i for i, (a, b) in enumerate(zip(got[33:108], wanted_camera)) if a != b],
                           hud=[i for i, (a, b) in enumerate(zip(got[108:110], wanted_hud)) if a != b])
        stage = got[31]
        stage_first.setdefault(stage, index + 1)
        if any(differences.values()):
            first = first or dict(callback=index + 1, stage=stage, differenceFields=differences)
            for domain, fields in differences.items():
                if fields:
                    first_by_domain.setdefault(domain, dict(callback=index + 1, stage=stage, fields=fields))
        if stage > 1 and index + 1 < stage_first[stage] + 16:
            windows.append(dict(callback=index + 1, stage=stage, controlFrame=got[1],
                                nativeControlFrame=want[0], differenceFields=differences,
                                scriptCallsDelta=int(got[23]) - want[22],
                                gameplayCallsDelta=int(got[25]) - want[24]))
    delivered = []
    events = run / 'delivery-events.u32'
    if events.exists():
        for event in struct.iter_unpack('<12I', raw(events)):
            kind, stage, generation, detail, _, _, _, _, low, high, callback, finished = event
            delivered.append(dict(kind=kind, stage=stage, generation=generation, detail=detail,
                                  callback=callback, initializationFinished=bool(finished),
                                  monotonicNs=low | high << 32))
    original_stores = []
    for line in raw(native / 'replay-rng-store-events.jsonl').splitlines():
        event = json.loads(line)
        original_stores.append(dict(stage=event['stage'], callback=event['precedingPlayerCallbacks'],
                                    pc=event['pc'], monotonicNs=event['hostMonotonicNs']))
    sleep_intervals = []
    pending_sleep = {}
    for event in original.get('transitionEvents', []):
        if event.get('event') == 'sleep60-before-call':
            assert event['requestedMilliseconds'] == 60
            pending_sleep[event['stage']] = event
        elif event.get('event') == 'sleep60-returned':
            begin = pending_sleep.pop(event['stage'])
            assert event['includesDebuggerPauseAtCallBoundary'] and event['returnInstructionObservedDirectly']
            sleep_intervals.append(dict(stage=event['stage'], requestedMilliseconds=60,
                                        callToReturnMilliseconds=(event['hostMonotonicNs']-begin['hostMonotonicNs'])/1e6,
                                        callbacksBetweenObservedBoundaries=event['precedingPlayerCallbacks']-begin['precedingPlayerCallbacks'],
                                        includesDebuggerPauseAtCallBoundary=True,
                                        ordinaryUninstrumentedSleepDurationAccepted=False))
    result = dict(schema='th14/independent-session-boundaries/1', liveSnapshotOnly=live,
                  callbacksCompared=compared, exactAll109WordPrefixCallbacks=(first['callback'] - 1 if first else compared),
                  firstDifference=first, firstDifferenceByDomain=first_by_domain,
                  stageEntriesCompared=stage_first, first16CallbacksPerLaterStage=windows,
                  independentDeliveryEvents=delivered, originalStoreEvents=original_stores,
                  nativeObservedSleepIntervals=sleep_intervals,
                  referenceValuesWrittenToEngine=False, rawStrictGatesSuperseded=False,
                  originalSchedulingAccepted=False, completeGame=False, bindings=bindings)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: result[k] for k in ['callbacksCompared', 'exactAll109WordPrefixCallbacks',
                                          'firstDifference', 'rawStrictGatesSuperseded', 'completeGame']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('run', 'native', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    main(args.run, args.native, args.output, args.live)
