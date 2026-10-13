"""Compare original emission inputs and exact bullet records without masking."""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','candidate','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();native_path,candidate_path,output=[(ROOT/x).resolve() for x in (a.native,a.candidate,a.output)]
    assert all(x.is_relative_to(ROOT/'artifacts/th14') for x in (native_path,candidate_path))
    assert output.is_relative_to(ROOT/'docs/porting')
    native,candidate=[json.loads(x.read_text()) for x in (native_path,candidate_path)]
    assert native['error']=='' and native['noInputInjection'] and native['childGameStateOverrides']==1
    observer=native['lateCollisionObserver']
    assert observer['fireObservationEnabled'] and SHA((native_path.parent/'capture-observer-source.py').read_bytes())==observer['toolSha256']
    for name,digest in candidate['sourceHashes'].items():assert SHA((ROOT/'runtimes/th12/th12_web'/name).read_bytes())==digest,name
    assert len(candidate['fires'])==len(native['bulletFires'])==117
    firing=[]
    for index,(actual,expected) in enumerate(zip(candidate['fires'],native['bulletFires'])):
        target=[expected['stageFrame'],expected['rateBits'],*expected['playerBits'],expected['exclusionBits'],*struct.unpack('<224I',bytes.fromhex(expected['emitter']))]
        assert len(actual)==len(target)==229
        firing.extend(dict(call=index,word=word,port=x,native=y) for word,(x,y) in enumerate(zip(actual,target)) if x!=y)
    rows={r['stageFrame']:r for r in native['frames']};bullet_differences=[]
    for actual in candidate['frames']:
        frame=actual['stageFrame'];expected=rows[frame]
        if sorted(actual['bulletDetails'])!=sorted(expected['bulletDetails']):
            bullet_differences.append(dict(frame=frame,port=actual['bulletDetails'],native=expected['bulletDetails']))
    assert len(candidate['frames'])==331
    bind=lambda path:dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    result=dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,
        emissionCalls=117,emissionWords=26793,emissionDifferentWords=len(firing),emissionDifferences=firing,
        comparedBulletFrames=331,bulletDifferentFrames=len(bullet_differences),bulletDifferences=bullet_differences,
        sourceFilesVerified=len(candidate['sourceHashes']),bindings=[bind(native_path),bind(candidate_path)],verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='All original emission parameters, live rate, player coordinates and exclusion values compared as raw229 words per call. Every bullet record compared as exact16-word multisets over the full331-frame window; no matching tolerance. Native warm case and read-only debugger instrumentation are declared. Linker interposition forwards unchanged arguments to the actual production function. Window equality is not whole-game, native transition, graphics/audio or object-memory equivalence.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('emissionCalls','emissionWords','emissionDifferentWords','comparedBulletFrames','bulletDifferentFrames')}))


if __name__=='__main__':main()
