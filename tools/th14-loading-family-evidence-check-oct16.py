"""Read stored loading-family evidence; never launch a game or its producers."""
import hashlib,json,struct
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
FIELDS=['stageFrame','held','pressed','x','y','lifeState','stateAge','transitionAge','shootingAge','invincibility','shotAge','focused','score','graze','pointValue','power','lives','lifePieces','bombs','bombPieces','rank','visualSeed','visualCalls','gameplaySeed','gameplayCalls','enemyCount','shots','character','subtype','difficulty','stage','scaleFlags']
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def hash_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(4*1024*1024):digest.update(block)
    return digest.hexdigest()
def main():
    doc=load(ROOT/'docs/porting/th14-loading-family-observed-oct16.json')
    assert doc['schema']=='th14-loading-family-evidence-v1'
    assert not doc['completeGame'] and not doc['nativeEquivalent']
    assert SHA(Path(__file__).read_bytes())==doc['checkerSha256']
    for name,row in doc['bindings'].items():
        path=(ROOT/name).resolve();assert path.is_relative_to(ROOT)
        assert path.stat().st_size==row['bytes'] and hash_file(path)==row['sha256'],name
    a=ROOT/'artifacts/th14';core=a/'loading-anm-candidate-core-v2-oct16'
    build=load(core/'build-result.json');assert build['compiled'] and build['sourceFiles']==267 and build['engineObjects']==141
    assert build['sourceChanges']==['cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp']
    for name,digest in build['sourceHashes'].items():assert hash_file(core/'source'/name)==digest,name
    for row in build['outputs']:assert Path(row['path']).stat().st_size==row['bytes'] and hash_file(row['path'])==row['sha256']
    for name in build['sourceChanges']:assert (ROOT/'runtimes/th12/th12_web'/name).read_bytes()==(core/'source'/name).read_bytes()
    assert build['sourceHashes']['cpp/game/ResourceCrypt.cpp']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    p=a/'loading-anm-candidate-playback-oct16';matrix=load(p/'all30-comparison.json')
    assert matrix['casesExecuted']==30 and matrix['totalCallbacks']==2853648
    assert matrix['naturalReplayEofCases']==27 and matrix['gameOverCases']==3
    counts=Counter();callbacks=0
    for case in matrix['cases']:
        key=case['key'];new=p/'playbacks'/key
        old=a/'royalflare-coverage-matrix-oct16'/('long-playbacks' if key=='reimub-easy' else 'playbacks')/key
        current=load(new/'receipt.json');before=load(old/'receipt.json')
        for name in ['callbacks','frames','currentQueueFullPlaybackVerified','gameOverRequested','stage','replaySha256']:assert current[name]==before[name],(key,name)
        assert not current['error'] and current['skipped']==current['unsupported']==0
        assert not current['forcedProgression'] and not current['invulnerabilityOverride']
        for name in ['callback-active.u8','enemy-owner.u8']:assert (new/name).read_bytes()==(old/name).read_bytes()
        raw=(new/'selected-state.u32').read_bytes();previous=(old/'selected-state.u32').read_bytes()
        assert len(raw)==len(previous)==current['callbacks']*128
        different=Counter()
        for got,want in zip(struct.iter_unpack('<32I',raw),struct.iter_unpack('<32I',previous)):
            for field,x,y in zip(FIELDS,got,want):
                if x!=y:different[field]+=1
        assert dict(different)==case['rawDifferenceCounts'],key
        if key.endswith('-extra'):assert raw==previous
        counts.update(different);callbacks+=current['callbacks']
    assert dict(counts)==matrix['allRawWordDifferenceCounts']=={'visualSeed':2289963,'visualCalls':2290193,'shots':225}
    assert callbacks==2853648
    increments=load(p/'loading-increments.json');assert len(increments)==175
    assert all(r['cppVisualIncrement']==r['nativeVisualIncrement'] for r in increments)
    assert sum(r['cppVisualIncrement'] for r in increments)==1252
    san=a/'loading-anm-candidate-sanitized-oct16';san_report=load(san/'report.json')
    assert san_report['passed'] and san_report['recompiledObjects']==141 and san_report['verifiedReusedObjects']==0
    assert san_report['nonrecoveringAddressAndUndefinedSanitizers']
    assert san_report['sourceHashes']==build['sourceHashes']
    for name,digest in san_report['objectHashes'].items():assert hash_file(san/'objects'/(name.replace('/','_')+'.o'))==digest
    assert sum(c['callbacks'] for c in san_report['cases'])==212679
    for case in san_report['cases']:
        key=case['key'];assert case['passed'] and case['gameOver'] and not case['naturalReplayEof'] and not case['errors']
        for suffix,name in [('state.u32','selected-state.u32'),('active.u8','callback-active.u8'),('owners.u8','enemy-owner.u8')]:assert (san/(key+'.'+suffix)).read_bytes()==(p/'playbacks'/key/name).read_bytes()
    sdl=a/'loading-anm-sdl-build-oct16';sdl_build=load(sdl/'build.json')
    assert sdl_build['compiled'] and len(sdl_build['objectHashes'])==len(sdl_build['recompiledSources'])==146
    assert sdl_build['exportsUnchanged'] and sdl_build['importsUnchanged']
    for group in ['sourceHashes','headerHashes']:
        for name,digest in sdl_build[group].items():assert hash_file(sdl/'source'/name)==digest
    for name,digest in sdl_build['objectHashes'].items():assert hash_file(sdl/name)==digest
    wasm='f798639ddabdc0be3b278dbf56fed2b43e4a27b78b964f8f9cddff5d3b4fb4ec'
    assert hash_file(sdl/'th11.wasm')==sdl_build['wasmSha256']==wasm
    assert (sdl/'th11.wasm').stat().st_size==1892277
    runtime=load(ROOT/'docs/porting/th14-launcher-runtime-loading-family-oct16.json')
    site=load(ROOT/'docs/porting/th14-launcher-site-loading-family-oct16.json')
    assert runtime['sourceSnapshotBound'] and not runtime['sameProductionWasm'] and not runtime['currentWorkspaceSourcesVerified']
    assert site['frozenLauncherReused'] and not site['sameProductionWasm']
    for report,folder in [(runtime,runtime['out']),(site,site['site'])]:
        for name,row in report['files'].items():
            path=Path(folder)/name;assert path.stat().st_size==row['bytes'] and hash_file(path)==row['sha256']
    assert len(runtime['files'])==40 and len(site['files'])==127
    qa=a/'loading-family-save-delta-qa-oct16';result=load(qa/'capture/report.json')
    assert result['passed'] and result['executedCases']==9 and all(c['passed'] for c in result['cases'])
    assert result['actualIndexedDb'] and result['actualEmscriptenFs'] and result['actualIdbfs']
    assert result['wasmSha256']==wasm and result['actualGameFrames']==result['gpuDraws']==0 and not result['audioPlayed']
    assert result['cases'][0]['newReplayDeleted'] and not result['cases'][7]['actualQuotaError']
    assert (qa/'delta.mjs').read_bytes()==(ROOT/'runtimes/th14/th14_web/browser-save-delta.mjs').read_bytes()
    assert (qa/'run.mjs').read_bytes()==(ROOT/'tools/th14-loading-family-save-delta-browser-check-oct16.mjs').read_bytes()
    quad=load(a/'reimub-captured-quad-check-oct16/all-comparisons.json')
    assert len(quad)==2781 and all(x['actual']==x['expected'] and x['currentVisible']==x['nativeVisible'] for x in quad)
    assert sum(len(x['actual']) for x in quad)==33372
    cross=load(a/'loading-family-cross-title-oct16/report.json')
    assert not cross['crossTitleCompilePassed'] and cross['baselineAndCandidateFailSameExistingSymbol']
    assert len(cross['rows'])==4 and all(x['exitCode']==1 and x['expectedUnchangedError'] for x in cross['rows'])
    browser=load(a/'loading-family-preview-oct16/reimub-stage4-corrected-observed.json')
    assert browser['visuallyObservedStage']==4 and browser['browserReplayNaturalTransitionsObserved']
    assert browser['outerQuietMarker'] and browser['innerQuietMarker'] and browser['audioZeroMsVisible']
    assert browser['saveConflictPresent'] and browser['warningAndErrorLogs']
    assert not browser['naturalReplayEofObserved'] and not browser['browserFramesInstrumented']
    assert not doc['actualBrowserStorageClean'] and doc['actualBrowserStorageConflictRetained']
    print(json.dumps(dict(storedEvidenceVerified=True,producerExecutedByChecker=False,matrixCases=30,callbacks=callbacks,naturalReplayEofCases=27,gameOverCases=3,loadingIncrementCallbacks=175,sanitizedCallbacks=212679,sanitizedObjects=141,sdlObjects=146,quadCases=2781,browserIsolatedStorageCases=9,actualBrowserStage=4,actualBrowserStorageConflictRetained=True,completeGame=False,nativeEquivalent=False)))
if __name__=='__main__':main()
