"""Revalidate the retained 30 ordinary-flow reports and saved-file identities.

Aggregates declared builds; does not claim a fresh single-build matrix, hardware
graphics, original complete playback, or score equality for the divergent case.
"""
from pathlib import Path
import hashlib
import json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/ordinary-difficulties-nov14'
SHA=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_bytes())


def main():
    groups={}
    bindings={}
    for difficulty in ('normal','extra','easy'):
        p=R/f'docs/porting/th14-ordinary-{difficulty}-loadouts-nov14.json'
        groups[difficulty]=load(p)['cases'];bindings[p.relative_to(R).as_posix()]=SHA(p.read_bytes())
    p=R/'docs/porting/th14-ordinary-higher-and-continue-nov14.json'
    higher=load(p)['cases']
    groups.update({k:higher[k] for k in ('hard','lunatic')});bindings[p.relative_to(R).as_posix()]=SHA(p.read_bytes())
    new=load(H/'alternate-three-score-qualified/report.json')
    assert new['allDeclaredFlowAndSaveCasesPassed'] and new['cases']==3
    for row in new['rows']:
        difficulty=row['key'].split('-')[1]
        groups[difficulty].append({**row,'freshReader':row['reader'],'finalScore':row['score']})
        codec_home='alternate-three-score-qualified' if difficulty=='easy' else 'higher-alternate-score-qualified-v1'
        codec=load(H/codec_home/(row['key']+'-native-codec.json'))
        assert codec['passed'] and codec['actualRetailDecryptAndLzss']
        assert codec['encodedSha256']==row['encodedSha256'] and codec['decodedSha256']==row['decodedSha256']
    rows=[]
    for difficulty,cases in groups.items():
        assert len(cases)==6,(difficulty,len(cases))
        assert {r['key'].split('-')[0] for r in cases}=={'reimua','reimub','marisaa','marisab','sakuyaa','sakuyab'}
        for row in cases:
            writer,reader=R/row['writer'],R/row['freshReader']
            a,b=load(writer/'report.json'),load(reader/'report.json')
            assert a['passed'] and b['passed'] and a['closed'] and b['closed']
            assert not a['exception'] and not b['exception'] and not a['errors'] and not b['errors']
            encoded=(writer/'save/scoreth14.dat').read_bytes()
            assert SHA(encoded)==row['encodedSha256']
            assert encoded==(reader/'save/scoreth14.dat').read_bytes()
            if 'writerReportSha256' in row:assert SHA((writer/'report.json').read_bytes())==row['writerReportSha256']
            if 'freshReportSha256' in row:assert SHA((reader/'report.json').read_bytes())==row['freshReportSha256']
            rows.append(dict(key=row['key'],writer=row['writer'],freshReader=row['freshReader'],
                             writerReportSha256=SHA((writer/'report.json').read_bytes()),
                             freshReportSha256=SHA((reader/'report.json').read_bytes()),
                             encodedSha256=row['encodedSha256'],finalScore=row['finalScore'],
                             writerWasmSha256=a.get('sourceWasmSha256',row.get('writerWasmSha256')),
                             declaredOrdinaryFlowAndFreshSavePassed=True))
    assert len(rows)==len({r['key'] for r in rows})==30
    q=dict(schema='th14/ordinary-flow-matrix/1',acceptanceStandard='observable-behavior-alignment',
           declaredOrdinaryFlowCases=30,freshReads=30,byDifficulty={k:len(v) for k,v in groups.items()},
           retainedReportsAndSaveIdentitiesRevalidated=True,aggregateAcrossDeclaredBuilds=True,
           singleCurrentBuildThirtyCaseMatrix=False,rows=rows,newAlternateCases=new['rows'],
           retainedEvidenceSha256=bindings,newQualificationSha256=SHA((H/'alternate-three-score-qualified/report.json').read_bytes()),
           newScoresRetailInstructionDecoded=True,newDecodedScoreBytes=3*149076,newScoreRecordChecksums=24,
           newAlternateAllReferenceScoresEqual=False,marisaBLunaticNewReferenceScoreDifference=4360,
           previousEarlyEndsAndDifferencesRetained=True,fullGpuFlowsAccepted=False,
           fullPublicBrowserFlowAccepted=False,allGameplayBehaviorAccepted=False,
           productionGameLogicChanged=False,newRuntimeDeployed=False,completeGame=False,
           toolSha256=SHA(Path(__file__).read_bytes()))
    diagnostic=H/'marisab-lunatic-alternate-stage-entry-comparison.json'
    if diagnostic.exists():
        d=load(diagnostic)
        assert d['postRunReadoutBaselineTerminalGameplayUnchanged'] and d['firstDifferentScoreEntryStage']==4
        assert not d['runtimeReferenceFeedback'] and not d['gameLogicChanged']
        assert d['toolSha256']==SHA((R/'tools/th14-compare-ordinary-stage-headers-nov14.py').read_bytes())
        q['newLunaticStageEntryDiagnostic']={k:v for k,v in d.items() if k!='selectedGameplayFields'}
        q['nextScoreInvestigation']='One extra graze during stage 3, first visible in the recorded stage-4 entry; exact in-stage frame not yet located.'
    target=R/'docs/porting/th14-ordinary-flow-matrix-nov14.json'
    tmp=target.with_name(target.name+'.new');tmp.write_text(json.dumps(q,indent=2)+'\n');tmp.replace(target)
    print(json.dumps({k:v for k,v in q.items() if k not in ('rows','newAlternateCases','retainedEvidenceSha256')}))


if __name__=='__main__':
    main()
