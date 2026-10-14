"""Bind the original growth write to before/after continuous replay evidence."""
import hashlib,importlib,json,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    bindings={}
    def read(name):
        p=ROOT/name;b=p.read_bytes();bindings[p.relative_to(ROOT).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    load=lambda name:json.loads(read(name))
    native=load('artifacts/th14/native-zps-reimua-lunatic-stage4-combat-oct14/reference.json')
    full=load('artifacts/th14/native-zps-reimua-lunatic-continuous-oct14/reference.compact.json')
    assert native['capturedFrames']==15900 and full['capturedFrames']==60000
    assert not native['timedOut'] and not full['timedOut'] and not native['error'] and not full['error']
    offset=next(i for i,r in enumerate(full['frames']) if r['selection']==[0,0,3,4] and r['stageFrame']==1 and r['player'][4]==0)
    def words(r):
        g,p=r['globals'],r['player']
        return [r['stageFrame'],r['held'],r['pressed'],*p[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],
                r['replayRng'][0],r['replayRng'][2],r['enemyCount'],r['shots'],*r['selection'],r['scaleFlags']]
    for a,b in zip(native['frames'],full['frames'][offset:offset+15900]):assert words(a)==words(b)
    before=load('artifacts/th14/custom-replay-reference/zps-reimua-lunatic-continuous-stage4-window-oct14/portable-details.json')
    after=load('artifacts/th14/custom-replay-reference/zps-reimua-lunatic-continuous-growth-window-oct14/portable-details.json')
    for label in ('zps-reimua-lunatic-continuous-stage4-window-oct14','zps-reimua-lunatic-continuous-growth-window-oct14'):
        report=load('docs/porting/th14-continuous-late-native-trace-'+label+'-observed-oct13.json')
        directory='artifacts/th14/custom-replay-reference/'+label
        assert SHA(read(directory+'/portable-details.json'))==report['rawDetailSha256']
        assert SHA(read(directory+'/portable-state.u32'))==report['portableStateSha256']
        assert SHA(read(directory+'/reference.wasm'))==report['wasmSha256']
        assert SHA(read(directory+'/late-combat-fixture.cpp'))==report['fixtureSha256']
        assert SHA(read('tools/th14-continuous-late-combat-trace-check.mjs'))==report['toolSha256']
        expected=load('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json' if 'growth-window' in label else 'artifacts/th14/pre-focused-growth-engine-oct14/engine-th14-build.json')
        assert expected['sourceHashes']==report['engineBuild']['sourceHashes']
    fields={'enemyDetails':'enemies','enemyPhaseDetails':'phases','liveShots':'shots','shotRewardCounters':'shotRewards'}
    checked=0;retained_rectangle_radius=0
    for n in native['frames']:
        if not 15820<=n['stageFrame']<=15890:continue
        p=after[offset+n['index']];assert p['active'] and p['stage']==4 and p['stageFrame']==n['stageFrame']
        for nk,pk in fields.items():assert n[nk]==p[pk],(n['stageFrame'],pk);checked+=1
        assert len(n['damageAreas'])==len(p['damageAreas'])
        for a,b in zip(n['damageAreas'],p['damageAreas']):
            if a!=b:
                # The standalone native capture starts with clean unused
                # radius fields; their continuous-native values are not known.
                assert not (a[1]&2) and all(x==y for j,(x,y) in enumerate(zip(a,b)) if j!=2)
                retained_rectangle_radius+=1
            else:checked+=1
    row=before[offset+15858];n=native['frames'][15858]
    pa=next(a for a in row['damageAreas'] if a[0]==23);na=next(a for a in n['damageAreas'] if a[0]==23)
    f=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
    assert (f(pa[2]),f(na[2]))==(152.,56.) and (pa[1]&3)==3
    assert before[offset+15859]['shotRewards'][1]==165 and n['shotRewardCounters'][1]==15
    engine=load('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')
    for name,digest in engine['sourceHashes'].items():assert SHA(read('runtimes/th12/th12_web/'+name))==digest
    playback=load('artifacts/th14/public-replay-playback/zps-reimua-lunatic-focused-growth-oct14/report.json')
    assert playback['sourceHashes']==engine['sourceHashes'] and playback['candidatePlaybackEnded'] and not playback['gameOverRequested']
    assert playback['frames']==90793 and not playback['error'] and not playback['unsupported'] and not playback['skipped']
    prefix=load('docs/porting/th14-reimua-lunatic-continuous-focused-growth-prefix-oct14.json')
    assert prefix['comparedCallbacks']==60000 and prefix['gameplayDifferences']==21
    assert prefix['fieldDifferenceCounts']['gameplayCalls']==21 and len(prefix['equalSelectedGameplayFields'])==29
    assert prefix['allRemainingGameplayDifferencesDuringInactiveLoading']
    img=importlib.import_module('th-anm-handlers').handlers(14)[0]
    instruction=img.read(0x451b34,13)
    assert instruction==bytes.fromhex('8b86c0000000c7401800000000')
    result=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,sourceFilesVerified=len(engine['sourceHashes']),
        nativeStage4Callbacks=15900,continuousNativeCallbacks=60000,continuousNativeStage4Start=offset,
        nativeStage4SelectedGameplayWordsEqual=15900*30,checkedDetailedFields=checked,
        standaloneVersusContinuousUnusedRectangleRadiusRows=retained_rectangle_radius,
        beforeFocusedRadius=152,expectedFocusedRadius=56,firstBattleDifferenceStage4Frame=15860,
        candidateCompleteLunaticFrames=90793,remainingLoadingGameplayCalls=21,
        nativeWrite=dict(address='0x451b3a',areaOffset='0x18',value=0,containingInstructions=instruction.hex(),executableSha256=SHA(img.data)),
        bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='The original focused spawn clears the actual reused area growth field. Production previously cleared only its shot-side copy. The before/after continuous production window is compared diagnostically with a standalone native stage4 window, after independently confirming all30 selected gameplay fields of that native stage agree with the separate uninterrupted native capture. Unused rectangle radius differences are counted and not certified as continuous-native object equality. Current60000-callback continuous native raw32 proof retains21 inactive-loading gameplay counter differences and visual RNG differences.90793-callback candidate completion is not full native/menu/pixels/audio/storage or whole-game1:1 proof. Declared warm initializations remain.')
    (ROOT/'docs/porting/th14-focused-area-growth-verified-oct14.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','scope')}))

if __name__=='__main__':main()
