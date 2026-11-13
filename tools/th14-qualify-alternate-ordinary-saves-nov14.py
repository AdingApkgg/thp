"""Qualify alternate ordinary campaigns without hiding reference-score differences.

Reads existing terminated Application runs and independently decodes their saves.
Does not run gameplay, alter input, or turn a score mismatch into acceptance.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/ordinary-difficulties-nov14'
SHA=lambda data:hashlib.sha256(data).hexdigest()
load=lambda p:json.loads(p.read_bytes())
CASES={
    'marisaa-hard':('marisaa-hard-full-alternate-k-g-v1','marisaa-hard-alternate-k-g-fresh-v1'),
    'marisab-lunatic':('marisab-lunatic-full-alternate-hachiji-v1','marisab-lunatic-alternate-hachiji-fresh-v1'),
    'marisaa-easy':('marisaa-easy-full-alternate-k-g-v4','marisaa-easy-alternate-k-g-fresh-v4'),
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--keys',nargs='+',choices=CASES,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    source=R/'tools/th14-audit-root-full-extra-nov08.py'
    fn=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='decode_score')
    spec=importlib.util.spec_from_file_location('mirror',R/'tools/th-replay-container.py')
    mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
    scope=dict(struct=struct,mirror=mirror)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec'),scope)
    component=R/'artifacts/th14/beam-length-guard-nov14/component'
    build=load(component/'build.json');wasm=SHA((component/'candidate.wasm').read_bytes())
    assert wasm==build['outputs']['candidate']['wasmSha256']
    for name,digest in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():
        assert SHA((R/name).read_bytes())==digest,name
    rows=[]
    for key in args.keys:
        writer,reader=[H/name for name in CASES[key]]
        a,b=load(writer/'report.json'),load(reader/'report.json')
        assert all(q['passed'] and q['retired'] and not q['exception'] and not q['errors'] for q in (a,b))
        assert a['sourceWasmSha256']==b['sourceWasmSha256']==wasm
        assert a['actualOrdinaryHeldInput'] and a['noRngStateWrites'] and not a['recordedGameStateRestored']
        assert not a['completionBoundaryInvokedDirectly'] and a['visitedStages']==[1,2,3,4,5,6]
        assert a['endingSeen'] and a['resultSeen'] and b['freshSavedTitleReadOnly']
        for folder,q in ((writer,a),(reader,b)):
            assert not load(folder/'platform.json')['audibleOutput']
            assert q['driverSha256']==SHA((folder/'executed-driver.mjs').read_bytes())
        assert load(writer/'ordinary-initial-player.json')['initialSeedMatched']
        meta=load(H/'higher-alternate-inputs'/(key+'-source.json'))
        assert meta['actualNativeCodecVerified'] and SHA((H/'higher-alternate-inputs'/(key+'.rpy')).read_bytes())==meta['sha256']
        selection=meta['character']*2+meta['subtype'];difficulty=meta['difficulty']
        encoded=(writer/'save/scoreth14.dat').read_bytes()
        assert encoded==(reader/'save/scoreth14.dat').read_bytes()
        decoded=scope['decode_score'](encoded);assert len(decoded)==149076
        for i in range(8):
            size=0x5298 if i<7 else 0x42c
            record=decoded[i*0x5298:i*0x5298+size]
            assert struct.unpack_from('<I',record)[0]==(0x15243 if i<7 else 0x15453)
            assert struct.unpack_from('<I',record,8)[0]==size
            assert sum(record[8:])==struct.unpack_from('<I',record,4)[0]
        offset=selection*0x5298
        for base in (0x7c0,0x7dc):
            assert list(struct.unpack_from('<5I',decoded,offset+base))==[int(i==difficulty) for i in range(5)]
        assert decoded[7*0x5298+0x16]==1
        clear_flags=1 if difficulty==0 else 17
        assert list(decoded[7*0x5298+0x17:7*0x5298+0x1d])==[clear_flags if i==selection else 0 for i in range(6)]
        rank=offset+0x10+difficulty*0x118
        result=load(writer/'natural-result-and-flush.json')
        score=struct.unpack_from('<I',decoded,rank)[0]*10
        reference=int(meta['archiveRow'][1].replace(',',''))
        assert score==result['rank']['scoreUnits']*10
        assert list(decoded[rank+4:rank+6])==[8,0]
        fresh=(reader/'score-observed.bin').read_bytes()
        assert len(fresh)==len(decoded) and fresh[rank:rank+0x118]==decoded[rank:rank+0x118]
        tape=load(writer/'observations-summary.json')
        assert tape['bytes']==tape['callbacks']*456 and not tape['fullTapePersisted']
        (out/(key+'-decoded.bin')).write_bytes(decoded)
        rows.append(dict(key=key,writer=writer.relative_to(R).as_posix(),reader=reader.relative_to(R).as_posix(),
                         score=score,sourceArchiveScore=reference,scoreDifference=score-reference,
                         referenceScoreEqual=score==reference,sourceReplaySha256=meta['sha256'],
                         sourceUrl=meta['download'],callbacks=tape['callbacks'],
                         encodedSha256=SHA(encoded),decodedSha256=SHA(decoded),
                         completeOrdinaryFlowAndFreshSavePassed=True,graphicsRecordingOnly=True,
                         hardwareVisualAccepted=False))
    (out/'scores.json').write_text(json.dumps(rows,indent=2)+'\n')
    q=dict(allDeclaredFlowAndSaveCasesPassed=True,allReferenceScoresEqual=all(r['referenceScoreEqual'] for r in rows),
           cases=len(rows),rows=rows,sourceWasmSha256=wasm,
           independentScoreRecordsDecoded=len(rows)*8,rawAssetsCopied=False,
           toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False)
    (out/'report.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))


if __name__=='__main__':
    main()
