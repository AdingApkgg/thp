"""Compare continuous production and actual retail callbacks without removing loading rows."""
import argparse,hashlib,json,struct
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()
FIELDS=['stageFrame','held','pressed','x','y','lifeState','stateAge','transitionAge','shootingAge','invincibility',
        'shotAge','focused','score','graze','pointValue','power','lives','lifePieces','bombs','bombPieces','rank',
        'visualSeed','visualCalls','gameplaySeed','gameplayCalls','enemyCount','shots','character','subtype','difficulty','stage','scaleFlags']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','playback','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();native_path,directory,output=[(ROOT/name).resolve() for name in (a.native,a.playback,a.output)]
    assert native_path.is_relative_to(ROOT/'artifacts/th14') and directory.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'docs/porting')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    bind=lambda path:dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    native,report=read(native_path),read(directory/'report.json');init=native['caseInitialization']
    assert native['error']=='' and native['noInputInjection'] and native['childGameStateOverrides']==1
    assert (init['address'],init['before'],init['after'],init['wordWrites'],init['replayManagerMode'])==('0x4f58b8',0x40,0,1,1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    assert SHA((ROOT/'tools/th14-native-stored-bootstrap-capture.py').read_bytes())==native['warmReplayCaptureToolSha256']
    assert report['physicalInvocationOrder'] and report['transitionCallbacksRetained']
    rt=ROOT/'runtimes/th12/th12_web'
    for name,digest in report['sourceHashes'].items():assert SHA((rt/name).read_bytes())==digest,name
    for name,key in [('th14-public-replay-physical-fixture.cpp','fixtureSha256'),('th14-custom-replay-reference-fixture.cpp','includedFixtureSha256'),('th14-session-reference-fixture.cpp','sessionFixtureSha256')]:
        assert SHA((rt/'tests/cpp'/name).read_bytes())==report[key]
    assert SHA((ROOT/'tools/th14-public-replay-physical-playback-check.mjs').read_bytes())==report['toolSha256']
    raw=(directory/'selected-state.u32').read_bytes();assert SHA(raw)==report['selectedStateSha256']
    actual=list(struct.iter_unpack('<32I',raw));assert len(actual)==report['selectedSamples']
    active_bytes=(directory/'callback-active.u8').read_bytes()
    assert len(active_bytes)==len(actual) and SHA(active_bytes)==report['callbackActiveSha256']
    assert SHA((directory/'public-replay.wasm').read_bytes())==report['wasmSha256']
    count=native['capturedFrames'];assert count==len(native['frames'])<=len(actual)
    differences=[];counts=Counter();first={};stages=Counter()
    for index,(row,observed) in enumerate(zip(native['frames'],actual)):
        assert row['index']==index
        g,player=row['globals'],row['player'];stages[row['selection'][3]]+=1
        expected=[row['stageFrame'],row['held'],row['pressed'],*player[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],
                  row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']]
        for field,(value,target) in enumerate(zip(observed,expected)):
            if value==target&0xffffffff:continue
            item=dict(index=index,stage=row['selection'][3],stageFrame=row['stageFrame'],field=FIELDS[field],port=value,native=target&0xffffffff)
            differences.append(item);counts[FIELDS[field]]+=1;first.setdefault(FIELDS[field],item)
    # Full differences are retained privately with a bound digest; this public
    # receipt does not hide the known startup visual or loading RNG counts.
    raw_differences=directory/'continuous-retail-differences.json';raw_differences.write_text(json.dumps(differences,separators=(',',':'))+'\n')
    gameplay=sum(value for field,value in counts.items() if field not in ('visualSeed','visualCalls'))
    remaining=[item for item in differences if item['field'] not in ('visualSeed','visualCalls')]
    result=dict(diagnosticOnly=True,passed=gameplay==0,completeGame=False,nativeEquivalent=False,
                physicalInvocationOrder=True,loadingCallbacksIncluded=True,comparedCallbacks=count,rawWords=count*32,
                stages=dict(stages),gameplayDifferences=gameplay,fieldDifferenceCounts=dict(counts),firstDifferences=first,
                remainingGameplayDifferences=remaining,
                equalSelectedGameplayFields=[field for field in FIELDS if field not in ('visualSeed','visualCalls') and not counts[field]],
                allRemainingGameplayDifferencesDuringInactiveLoading=all(not active_bytes[item['index']] for item in remaining),
                nativeCaptureTimedOut=native['timedOut'],nativeElapsedSeconds=native['elapsedSeconds'],nativeCaseInitialization=init,
                candidatePlaybackEnded=report['candidatePlaybackEnded'],allDifferences=bind(raw_differences),sourceFilesVerified=len(report['sourceHashes']),
                bindings=[bind(path) for path in (native_path,directory/'report.json',directory/'selected-state.u32',directory/'callback-active.u8',directory/'public-replay.wasm')],
                verifierSha256=SHA(Path(__file__).read_bytes()),
                scope='Every continuous original retail callback is paired in physical order with production, including inactive loading, stage-clock resets, repeated clocks and transition-boundary rows. No stage slicing, resynchronization, input/RNG fixes in the oracle, row removal or masking of gameplay differences. All raw32 differences retained with digest. One declared initial warm replay flag clear remains; this prefix does not certify ordinary menu startup, whole-game completion, object-owner memory, pixels/audio or storage.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','comparedCallbacks','gameplayDifferences','fieldDifferenceCounts')}))
    if gameplay:raise SystemExit(1)

if __name__=='__main__':main()
