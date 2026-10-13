"""Compare every sampled continuous-production word with independent retail stages.

These warm stage starts cannot certify uninterrupted native transitions. Keep
all field differences and explicitly report missing transition-boundary rows.
"""
import argparse, hashlib, json, struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
FIELDS = ['stageFrame','held','pressed','x','y','lifeState','stateAge',
          'transitionAge','shootingAge','invincibility','shotAge','weaponMode',
          'score','graze','pointValue','power','lives','lifePieces','bombs',
          'bombPieces','rank','visualSeed','visualCalls','gameplaySeed','gameplayCalls',
          'enemyCount','shots','character','subtype','difficulty','stage','scaleFlags']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--playback', required=True)
    p.add_argument('--native', action='append', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    directory = (ROOT/a.playback).resolve()
    output = (ROOT/a.output).resolve()
    assert directory.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'docs/porting')
    bind = lambda path: dict(path=str(path.relative_to(ROOT)).replace('\\','/'),
                             bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    report = json.loads((directory/'report.json').read_text())
    raw = (directory/'selected-state.u32').read_bytes()
    assert SHA(raw) == report['selectedStateSha256']
    actual = list(struct.iter_unpack('<32I', raw))
    assert len(actual) == report['selectedSamples']
    active_bytes = (directory/'callback-active.u8').read_bytes()
    assert SHA(active_bytes)==report['callbackActiveSha256'] and len(active_bytes)==len(actual)
    assert all(value in (0,1) for value in active_bytes)
    assert sum(value==0 for value in active_bytes)==report['inactiveCallbacksRetained']
    for name, digest in report['sourceHashes'].items():
        assert SHA((ROOT/'runtimes/th12/th12_web'/name).read_bytes()) == digest, name
    assert SHA((ROOT/'tools/th14-public-replay-physical-playback-check.mjs').read_bytes()) == report['toolSha256']
    for name,key in [('th14-public-replay-physical-fixture.cpp','fixtureSha256'),('th14-custom-replay-reference-fixture.cpp','includedFixtureSha256'),('th14-session-reference-fixture.cpp','sessionFixtureSha256')]:
        assert SHA((ROOT/'runtimes/th12/th12_web/tests/cpp'/name).read_bytes()) == report[key]
    assert SHA((directory/'public-replay.wasm').read_bytes()) == report['wasmSha256']
    assert report['unsupported']==report['skipped']==0 and not report['error']
    stages = []
    bindings = [bind(directory/'report.json'),bind(directory/'selected-state.u32'),bind(directory/'callback-active.u8')]
    for name in a.native:
        path = (ROOT/name).resolve()
        assert path.is_relative_to(ROOT/'artifacts/th14')
        native = json.loads(path.read_text())
        assert native['error'] == '' and native['noInputInjection']
        assert native['childGameStateOverrides'] == 1
        assert not native['ordinaryMenuLoaderVerified'] and not native['completeGame']
        stage = native['frames'][0]['selection'][3]
        expected = []
        for row in native['frames']:
            assert row['selection'] == native['frames'][0]['selection']
            g, player = row['globals'], row['player']
            words = [row['stageFrame'],row['held'],row['pressed'],*player[:9],
                     g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],
                     row['scriptRng'][0],row['scriptRng'][2],
                     row['replayRng'][0],row['replayRng'][2],
                     row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']]
            assert row['index'] == len(expected)
            expected.append(tuple(v & 0xffffffff for v in words))
        assert report['physicalInvocationOrder'] and report['transitionCallbacksRetained']
        observed = [row for row,active in zip(actual,active_bytes) if row[30] == stage and active]
        inactive = [index for index,(row,active) in enumerate(zip(actual,active_bytes)) if row[30] == stage and not active]
        count = min(len(expected),len(observed))
        counts, first = Counter(), {}
        for index,(row,target_row) in enumerate(zip(observed,expected)):
            for field,(value,target) in enumerate(zip(row,target_row)):
                if value != target:
                    key = FIELDS[field]
                    counts[key] += 1
                    first.setdefault(key,dict(physicalIndex=index,nativeStageFrame=target_row[0],portStageFrame=row[0],port=value,native=target))
        stages.append(dict(stage=stage,comparedFrames=count,
                           rawWords=count*32,fieldDifferenceCounts=dict(counts),
                           firstDifferences=first,
                           missingNativeInvocationIndices=list(range(count,len(expected))),
                           productionRowsBeyondNativePrefix=len(observed)-count,
                           retainedInactiveProductionInvocationIndices=inactive,
                           repeatedNativeStageClockRows=sum(i>0 and row[0]==expected[i-1][0] for i,row in enumerate(expected)),
                           nativeCaptureTimedOut=native['timedOut'],
                           nativeCaseInitialization=native['caseInitialization']))
        bindings.append(bind(path))
    result = dict(diagnosticOnly=True,physicalInvocationOrder=True,completeGame=False,nativeEquivalent=False,
                  uninterruptedNativeTransitionsVerified=False,
                  candidatePlaybackEnded=report['candidatePlaybackEnded'],
                  gameOverRequested=report['gameOverRequested'],
                  playbackFrames=report['frames'],allProductionCallbacks=len(actual),inactiveCallbacksRetained=report['inactiveCallbacksRetained'],stages=stages,bindings=bindings,
                  verifierSha256=SHA(Path(__file__).read_bytes()),
                  scope='Every available raw32 sample recomputed directly from independent warm retail stage captures. All field differences retained. Native stage startup differs from uninterrupted production loading; pressed edges are differences, not masked. Every fresh production Player callback is retained, including last transition rows and repeated scaled clocks. Native captures begin at stage activation. Their rows are paired with callbacks whose observer-time stage_active flag is set, by stage and physical invocation ordinal. All inactive loading callbacks remain in the raw stream and their indices are listed separately, outside this active baseline. No clock-key map, resynchronization, deletion or deduplication. Extra production rows outside the original capture remain outside the verified prefix. No full native transition, ending, graphics/audio or complete-game equivalence claim.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(playbackFrames=result['playbackFrames'],
                          gameOver=result['gameOverRequested'],
                          stages=[dict(stage=s['stage'],frames=s['comparedFrames'],
                                       counts=s['fieldDifferenceCounts'],missing=s['missingNativeInvocationIndices'],extra=s['productionRowsBeyondNativePrefix'])
                                  for s in stages])))


if __name__ == '__main__':
    main()
