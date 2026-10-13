"""Independently compare all retained scalar and captured object observations."""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtimes/th12/th12_web'
SHA=lambda data:hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True)
    a=p.parse_args()
    assert a.label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.label)
    bindings={}
    def read(path):
        path=ROOT/path
        data=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
        return data
    load=lambda path:json.loads(read(path))
    report=load('docs/porting/th14-physical-replay-native-trace-'+a.label+'-observed-oct13.json')
    assert report['passed'] and not report['differences'] and not report['detailDifferences']
    assert report['physicalInvocationOrder'] and not report['absentPlayerObservations']
    native_bytes=read(report['nativeTracePath']);assert SHA(native_bytes)==report['nativeTraceSha256']
    native=json.loads(native_bytes)
    assert native['error']=='' and not native['timedOut'] and native['noInputInjection']
    assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert native['childGameStateOverrides']==1 and not native['ordinaryMenuLoaderVerified']
    init=native['caseInitialization'];assert (init['before'],init['after'],init['wordWrites'])==(0x40,0,1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    assert SHA(read('tools/th14-native-stored-bootstrap-capture.py'))==native['warmReplayCaptureToolSha256']
    assert SHA(read('tools/th14-native-first-loader-angle-capture.py'))==native['lateCollisionObserver']['toolSha256']
    for name,digest in report['engineBuild']['sourceHashes'].items():assert SHA(read(RT.relative_to(ROOT)/name))==digest,name
    directory='artifacts/th14/custom-replay-reference/'+a.label
    raw=read(directory+'/portable-state.u32');assert SHA(raw)==report['portableStateSha256']
    values=list(struct.iter_unpack('<32I',raw));assert len(values)==native['capturedFrames']==report['comparedFrames']
    visual=0
    for index,(row,words) in enumerate(zip(native['frames'],values)):
        assert row['index']==index and row['selection']==[0,0,4,7]
        g,player=row['globals'],row['player']
        expected=[row['stageFrame'],row['held'],row['pressed'],*player[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],
                  row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']]
        for field,(value,target) in enumerate(zip(words,expected)):
            if value==target&0xffffffff:continue
            if field in (21,22):visual+=1
            else:raise AssertionError((index,field,value,target))
    assert visual==len(report['startupVisualDifferences'])
    details_bytes=read(report['rawDetailPath']);assert SHA(details_bytes)==report['rawDetailSha256']
    details=json.loads(details_bytes);assert len(details)==len(values)
    fields={'popupWords':'popupWords','enemyDetails':'enemies','enemyPhaseDetails':'phases','liveShots':'shots',
            'itemDetails':'items','bulletDetails':'bullets','enemyIds':'enemyIds','shotRewardCounters':'shotRewards',
            'damageAreas':'damageAreas','popupCursor':'popupCursor','enemyNextId':'enemyNextId','enemyHitboxAngles':'enemyHitboxAngles'}
    checked,angles=0,0
    for index,(row,observed) in enumerate(zip(native['frames'],details)):
        assert observed['index']==index and observed['stageFrame']==row['stageFrame']
        for name,key in fields.items():
            if name not in row:continue
            left,right=observed[key],row[name]
            if key in ('items','bullets'):left,right=sorted(left),sorted(right)
            assert left==right,(index,key)
            checked+=1
            if key=='enemyHitboxAngles':angles+=len(right)
    assert angles>0
    assert SHA(read(directory+'/reference.wasm'))==report['wasmSha256']
    assert SHA(read(directory+'/late-combat-fixture.cpp'))==report['fixtureSha256']
    assert SHA(read('tools/th14-late-combat-shared-angle-trace-check.mjs'))==report['toolSha256']
    result=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,callbacks=len(values),rawWords=len(values)*32,
                gameplayDifferences=0,visualDifferences=visual,independentlyRecomputedDetailFields=checked,
                independentlyComparedAngleWords=angles,lateWindow=report['lateObservationWindow'],bindings=bindings,
                verifierSha256=SHA(Path(__file__).read_bytes()),
                scope='Every physical raw32 callback and every captured detailed field is independently recomputed from retained original-process and production bytes. Visual RNG differences remain counted separately; they are not an all-fields pass. Enemy rotation words share the original+120 ANM/ECL/damage storage. One declared40->0 warm mode initialization remains. This prefix does not certify full Extra/menu/ending, original pixels/audio, storage or whole-game1:1.')
    (ROOT/('docs/porting/th14-late-combat-'+a.label+'-verified-oct14.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))


if __name__=='__main__':main()
