"""Independently retain late native/candidate collision and bullet differences."""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','candidate','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();paths=[(ROOT/x).resolve() for x in (a.native,a.candidate,a.output)]
    native_path,candidate_path,output=paths
    assert all(x.is_relative_to(ROOT/'artifacts/th14') for x in paths[:2])
    assert output.is_relative_to(ROOT/'docs/porting')
    native,candidate=[json.loads(x.read_text()) for x in paths[:2]]
    assert native['error']=='' and native['noInputInjection']
    assert native['childGameStateOverrides']==1 and not native['ordinaryMenuLoaderVerified']
    assert (native['caseInitialization']['before'],native['caseInitialization']['after'])==(0x44,4)
    observer=native['lateCollisionObserver']
    assert SHA((native_path.parent/'capture-observer-source.py').read_bytes())==observer['toolSha256']
    for name,digest in candidate['sourceHashes'].items():
        assert SHA((ROOT/'runtimes/th12/th12_web'/name).read_bytes())==digest,name
    rows={r['stageFrame']:r for r in native['frames']}
    differences=[];first_collision=None
    key=lambda b:(b[6],b[7],b[13],b[14])
    for actual in candidate['frames']:
        frame=actual['stageFrame'];expected=rows[frame]
        d=expected['collisionDiagnostic']
        target=d['playerFloatBits']+d['hitBoundsBits']+[d['scaleFactorBits'],d['scaleFlags']]
        collision=[dict(field=i,port=x,native=y) for i,(x,y) in enumerate(zip(actual['collisionDiagnostic'],target)) if x!=y]
        if collision and first_collision is None:first_collision=frame
        ab,nb=actual['bulletDetails'],expected['bulletDetails']
        # Matching is diagnostic only. Exact multiset differences below do
        # not rely on this velocity/age/appearance heuristic.
        ak,nk=[key(b) for b in ab],[key(b) for b in nb]
        assert len(set(ak))==len(ak) and len(set(nk))==len(nk)
        lookup=dict(zip(nk,nb))
        shared=[dict(key=list(key(b)),port=b,native=lookup[key(b)]) for b in ab if key(b) in lookup and b!=lookup[key(b)]]
        ac,nc=Counter(map(tuple,ab)),Counter(map(tuple,nb))
        differences.append(dict(frame=frame,collisionDifferences=collision,
            portBulletCount=len(ab),nativeBulletCount=len(nb),
            exactPortOnlyRecords=sum((ac-nc).values()),exactNativeOnlyRecords=sum((nc-ac).values()),
            heuristicPortOnlyRecords=[b for b in ab if key(b) not in lookup],
            heuristicNativeOnlyRecords=[b for b in nb if key(b) not in set(ak)],
            heuristicSharedDifferences=shared))
    assert len(differences)==observer['last']-observer['first']+1
    binding=lambda path:dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    result=dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,
        frames=len(differences),firstCollisionDiagnosticDifference=first_collision,
        differences=differences,bindings=[binding(path) for path in paths[:2]],
        verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='Direct raw collision-bit and exact bullet multiset comparison for every captured window frame. All differences retained. Velocity/age/appearance matching is a diagnostic heuristic only, not native object identity. Native capture has one declared warm initialization and read-only instrumentation of an owned child. No completion/equivalence claim.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(frames=len(differences),firstCollisionDiagnosticDifference=first_collision,
                          firstFrameBulletCounts=[differences[0]['portBulletCount'],differences[0]['nativeBulletCount']],
                          firstFrameHeuristicExtra=len(differences[0]['heuristicPortOnlyRecords']))))


if __name__=='__main__':main()
