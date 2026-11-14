"""Compare actual retail and port Player tapes without rewriting either tape.

Both tapes use the retained 32-word pre-Player observation schema. Last-key
pairing is diagnostic: original callback and stage-handoff differences remain
in the report and cannot establish complete scheduling equivalence.
"""
from pathlib import Path
import argparse,array,hashlib,json,sys

R=Path(__file__).resolve().parents[1]
NAMES=['controlFrame','movementHeld','movementPressed','x','y','lifeState',
       'stateTimer','transitionTimer','shootingAge','invincibility','shotTimer',
       'weaponMode','scoreUnits','graze','pointValue','power','lives','lifeFragments',
       'bombs','bombFragments','rank','scriptSeed','scriptCalls','visualSeed','visualCalls',
       'enemies','playerShots','character','subtype','difficulty','stage','scaleFlags']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def read_tape(path):
    data=path.read_bytes();assert data and len(data)%128==0
    a=array.array('I');a.frombytes(data)
    if sys.byteorder!='little':a.byteswap()
    return [a[i:i+32] for i in range(0,len(a),32)]

def compare(native,port,stage,allowNaturalEarlyEnd=False):
    nativeReport=json.loads((native/'report.json').read_bytes())
    portReport=json.loads((port/'report.json').read_bytes())
    assert nativeReport['realOriginalWindowsProcess'] and nativeReport['instructionBytesPatched']==0
    assert not nativeReport['error'] and not nativeReport['debugErrors'] and nativeReport['childExited']
    assert nativeReport['rngOrCounterWrites']==0
    assert nativeReport['sourceFullReplaySha256']==portReport['inputSha256']
    config=bytes.fromhex(nativeReport['configHex']);assert config[0x22]==config[0x23]==0
    assert portReport['retired'] and not portReport['errors']
    retainedAssertion=None
    if not portReport['passed']:
        assert allowNaturalEarlyEnd and portReport.get('diagnosticOnly') and portReport.get('selectedStage3ToStage4Only')
        assert portReport['exception'].startswith('AssertionError [ERR_ASSERTION]')
        checkpoint=json.loads((port/'checkpoint-stage4-entry.json').read_bytes())
        observed=json.loads((port/'diagnostic-player-samples.json').read_bytes())
        assert checkpoint['native'][3:5]==[1,2] and checkpoint['native'][0]==stage
        assert observed['postCallbackOutcome'][2]==0xffffffff
        retainedAssertion=portReport['exception']
    else:assert not portReport['exception']
    assert json.loads((port/'platform.json').read_bytes())['audibleOutput'] is False
    rows=[read_tape(folder/'selected-state.u32') for folder in [native,port]]
    assert len(rows[0])==nativeReport['callbacks']
    maps=[];duplicates=[]
    for tape in rows:
        m={};dupes=0
        for i,row in enumerate(tape):
            if row[30]!=stage:continue
            key=row[0];dupes+=key in m;m[key]=(i+1,row)
        assert m,'selected stage absent'
        maps.append(m);duplicates.append(dupes)
    common=sorted(maps[0].keys()&maps[1].keys());assert common
    first={};counts={};firstGrazeWindow=[]
    for frame in common:
        ni,a=maps[0][frame];pi,b=maps[1][frame]
        for k,name in enumerate(NAMES):
            if a[k]==b[k]:continue
            counts[name]=counts.get(name,0)+1
            first.setdefault(name,{'controlFrame':frame,'nativeCallback':ni,'portCallback':pi,
                                   'native':a[k],'port':b[k]})
    if 'graze' in first:
        center=first['graze']['controlFrame']
        for frame in common:
            if abs(frame-center)>4:continue
            ni,a=maps[0][frame];pi,b=maps[1][frame]
            firstGrazeWindow.append({'frame':frame,'nativeCallback':ni,'portCallback':pi,
                'native':{NAMES[k]:a[k] for k in [1,2,3,4,5,9,12,13,14,25,26]},
                'port':{NAMES[k]:b[k] for k in [1,2,3,4,5,9,12,13,14,25,26]}})
    observable=[n for n in NAMES if n not in ['scriptSeed','scriptCalls','visualSeed','visualCalls']]
    firstObservable=min(({'field':n,**first[n]} for n in observable if n in first),
                        key=lambda r:r['controlFrame'],default=None)
    return {'schema':'th14/stage-trajectory-comparison/1','auditCompleted':True,'stage':stage,
            'pairedStageFrames':len(common),'frameRange':[common[0],common[-1]],
            'nativeCallbacks':len(rows[0]),'portCallbacks':len(rows[1]),
            'nativeDuplicateStageFrameKeys':duplicates[0],'portDuplicateStageFrameKeys':duplicates[1],
            'pairing':'last occurrence of stage/control frame, diagnostic only; raw tapes unchanged',
            'firstObservableDifference':firstObservable,'firstByField':first,'differenceCounts':counts,
            'firstGrazeWindow':firstGrazeWindow,
            'nativeCaptureBoundaryReached':nativeReport.get('diagnosticStageBoundaryReached',False),
            'portRequestedBoundaryPassed':portReport['passed'],'portOriginalAssertionRetained':retainedAssertion,
            'nativeInputSha256':nativeReport['sourceFullReplaySha256'],
            'portInputSha256':portReport['inputSha256'],
            'nativeTapeSha256':sha(native/'selected-state.u32'),'portTapeSha256':sha(port/'selected-state.u32'),
            'nativeReportSha256':sha(native/'report.json'),'portReportSha256':sha(port/'report.json'),
            'originalInstructionBytesPatched':0,'runtimeReferenceFeedback':False,'silent':True,
            'allModesAccepted':False,'fullGpuAccepted':False,'completeGame':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['native','port','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--stage',type=int,choices=range(1,8),required=True)
    p.add_argument('--allow-natural-early-end',action='store_true',help='Compare this bounded diagnostic tape after verified natural GameOver, retaining its failed stage4 expectation')
    a=p.parse_args();assert a.output.resolve().is_relative_to(R/'artifacts/th14') and not a.output.exists()
    q=compare(a.native,a.port,a.stage,a.allow_natural_early_end);q['toolSha256']=sha(Path(__file__))
    a.output.write_text(json.dumps(q,indent=2)+'\n')
    print(json.dumps({k:q[k] for k in ['auditCompleted','pairedStageFrames','firstObservableDifference','firstByField']}))

if __name__=='__main__':main()
