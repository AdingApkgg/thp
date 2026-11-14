"""Audit replay carry before the next stage header overwrites gameplay state.

The input tape is the existing 32-word Player observation schema. This is an
offline audit, with no writes to a replay, game state, or reference result.
"""
from pathlib import Path
import argparse,array,hashlib,json,struct,sys

R=Path(__file__).resolve().parents[1]
FIELDS={'scoreUnits':(12,2),'graze':(13,6),'pointValue':(14,9),'power':(15,12),
        'lives':(16,15),'lifeFragments':(17,16),'bombs':(18,18),'bombFragments':(19,19)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def audit(run,decoded):
    report=json.loads((run/'report.json').read_bytes())
    assert report['passed'] and report['retired'] and not report['exception'] and not report['errors']
    assert json.loads((run/'platform.json').read_bytes())['audibleOutput'] is False
    assert sha(run/'executed-driver.mjs')==report['driverSha256']
    data=decoded.read_bytes();count=struct.unpack_from('<I',data,0x78)[0]
    assert 1<=count<=7
    headers={};offset=0x94
    for _ in range(count):
        stage,seed,frames,payload=struct.unpack_from('<HHII',data,offset)
        assert 1<=stage<=7 and stage not in headers and offset+0xdc+payload<=len(data)
        headers[stage]=struct.unpack_from('<28I',data,offset+0x14)
        offset+=0xdc+payload
    assert offset==len(data)
    a=array.array('I');a.frombytes((run/'selected-state.u32').read_bytes())
    if sys.byteorder!='little':a.byteswap()
    assert len(a)%32==0 and a
    rows=[a[i:i+32] for i in range(0,len(a),32)]
    transitions=[];priorStage=rows[0][30]
    for i,row in enumerate(rows):
        stage=row[30]
        if stage==priorStage:continue
        assert stage==priorStage+1 and stage in headers
        reference=headers[stage]
        differences={n:{'reference':reference[h],'carry':row[t]}
                     for n,(t,h) in FIELDS.items() if row[t]!=reference[h]}
        # The original player survives while the next stage is loading. Its
        # first frame-1 record with reset Player clocks identifies the new one.
        fresh=next(((j,r) for j,r in enumerate(rows[i:],i)
                    if r[30]==stage and r[0]==1 and r[6]==0 and r[7]==0),None)
        restoredDifferences=None
        if fresh:
            restoredDifferences={n:{'reference':reference[h],'restored':fresh[1][t]}
                                 for n,(t,h) in FIELDS.items() if fresh[1][t]!=reference[h]}
        transitions.append({'fromStage':priorStage,'toStage':stage,'carryCallback':i+1,
                            'carryControlFrame':row[0],'differences':differences,
                            'freshPlayerCallback':fresh[0]+1 if fresh else None,
                            'afterRestoreDifferences':restoredDifferences,
                            'differenceMaskedByHeaderRestore':bool(differences) and restoredDifferences=={}})
        priorStage=stage
    assert transitions,'no natural stage transition in supplied tape'
    return {'schema':'th14/replay-carry-audit/1','auditCompleted':True,
            'observedCarryAlignmentPassed':all(not x['differences'] for x in transitions),
            'transitions':transitions,'comparedFields':list(FIELDS),
            'selectedTapeSha256':sha(run/'selected-state.u32'),'decodedSha256':sha(decoded),
            'runReportSha256':sha(run/'report.json'),'inputSha256':report['inputSha256'],
            'scope':'declared selected Player/economy fields at observed natural transitions; not all replay state or full-game proof',
            'recordingInterfaceGraphicsOnly':True,'silent':True,'gameStateModified':False,'completeGame':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['run','decoded','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert a.output.resolve().is_relative_to(R/'artifacts/th14') and not a.output.exists()
    q=audit(a.run,a.decoded);q['toolSha256']=sha(Path(__file__))
    a.output.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))
    return 0 if q['observedCarryAlignmentPassed'] else 2

if __name__=='__main__':sys.exit(main())
