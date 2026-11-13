"""Locate stage-entry gameplay differences using a post-run recording readout.

The baseline run must retain the same selected terminal gameplay and callback
count. This is an offline diagnostic, not an oracle feeding state into play.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FIELDS={'scoreUnits':2,'difficulty':3,'continues':4,'rank':5,'graze':6,
        'pointItems':8,'pointValue':9,'minimumPointValue':10,'maxPointValue':11,
        'power':12,'maxPower':13,'powerStep':14,'lives':15,'lifeFragments':16,
        'lifeAwards':17,'bombs':18,'bombFragments':19,'comboTotal':20,
        'comboCount':22,'comboTimer':23,'specialDropCount':27}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('decoded','baseline','observed','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert a.output.resolve().is_relative_to(ROOT/'artifacts/th14') and not a.output.exists()
    base,seen=load(a.baseline/'report.json'),load(a.observed/'report.json')
    assert all(r['passed'] and r['retired'] and not r['exception'] and not r['errors'] for r in (base,seen))
    before,after=load(a.baseline/'observations-summary.json'),load(a.observed/'observations-summary.json')
    assert before['callbacks']==after['callbacks']
    gameplay=list(range(21))+list(range(25,31))
    for boundary in ('first','last'):
        assert [before[boundary][i] for i in gameplay]==[after[boundary][i] for i in gameplay],boundary
    original_result=load(a.baseline/'natural-result-and-flush.json')
    observed_result=load(a.observed/'natural-result-and-flush.json')
    assert original_result['rank']==observed_result['rank']
    assert load(a.baseline/'before-close.json')['stageSeeds']==load(a.observed/'before-close.json')['stageSeeds']
    raw=a.decoded.read_bytes();headers=(a.observed/'recorded-stage-headers.bin').read_bytes()
    assert len(headers)==8*0xdc
    count=struct.unpack_from('<I',raw,0x78)[0];assert count==6
    offset=0x94;rows=[]
    for _ in range(count):
        stage,seed,frames,payload=struct.unpack_from('<HHII',raw,offset)
        reference=raw[offset:offset+0xdc];actual=headers[stage*0xdc:(stage+1)*0xdc]
        assert struct.unpack_from('<HH',actual)==(stage,seed)
        ref_values=struct.unpack_from('<28I',reference,0x14)
        got_values=struct.unpack_from('<28I',actual,0x14)
        differences={name:dict(reference=ref_values[index],ordinary=got_values[index])
                     for name,index in FIELDS.items() if ref_values[index]!=got_values[index]}
        rows.append(dict(stage=stage,sourceFrames=frames,referenceScore=ref_values[2]*10,
                         ordinaryScore=got_values[2]*10,scoreDifference=(got_values[2]-ref_values[2])*10,
                         selectedGameplayDifferences=differences))
        offset+=0xdc+payload
    assert offset==len(raw)
    first_score=next((r['stage'] for r in rows if r['scoreDifference']),None)
    q=dict(postRunReadoutBaselineTerminalGameplayUnchanged=True,selectedGameplayFields=gameplay,
           baselineCallbacks=before['callbacks'],stageEntryRows=rows,firstDifferentScoreEntryStage=first_score,
           finalOrdinaryScore=observed_result['rank']['scoreUnits']*10,
           decodedSha256=sha(a.decoded),recordedHeadersSha256=sha(a.observed/'recorded-stage-headers.bin'),
           baselineReportSha256=sha(a.baseline/'report.json'),observedReportSha256=sha(a.observed/'report.json'),
           firstDivergentInStageFrameLocated=False,originalWholeGameReplayed=False,
           runtimeReferenceFeedback=False,gameLogicChanged=False,completeGame=False,toolSha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))


if __name__=='__main__':
    main()
