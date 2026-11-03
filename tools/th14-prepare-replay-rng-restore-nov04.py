"""Freeze the RNG store-order candidate while preserving production sources."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir()
    b=R/'artifacts/th14/camera-publication-candidate-v3-nov04/production-core/observer-build.json'
    base=json.loads(b.read_bytes());assert base['sourcePublishedCommit']=='2b0bc1c67ddeb57aa7ce2208f08cbf08ffc8bdda'
    source=out/'source';parent=Path(base['sourceSnapshotRoot'])
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        raw=(parent/name).read_bytes();assert sha(raw)==digest,name
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    changes=[]
    def edit(name,replacements):
        path=source/'th12_web/cpp/game'/name;raw=path.read_bytes();text=raw.decode().replace('\r\n','\n')
        for old,new,count in replacements:
            assert text.count(old)==count,(name,old,text.count(old));text=text.replace(old,new)
        ending='\r\n'if raw.count(b'\r\n')==raw.count(b'\n')and b'\r\n'in raw else'\n'
        path.write_bytes(text.replace('\n',ending).encode());changes.append(dict(path='th12_web/cpp/game/'+name,beforeSha256=sha(raw),afterSha256=sha(path.read_bytes())))
    edit('Replay.cpp',[
        ('#include "Rng.hpp"','#include "Rng.hpp"\n#if PORT_TITLE == 14\n#include "ReplayRngRestoreTh14.hpp"\n#endif',1),
        ('    rng.seed=u16(seed);rng.calls=0;\n#if PORT_TITLE == 14','''#if PORT_TITLE == 14
    th14_restore_replay_rng(rng,visual,seed,first);''',1),
        ('    if(visual&&!first)visual->seed=u16(seed);\n','',1),
        ('    (void)visual;\n    // The title\'s own restore','    rng.seed=u16(seed);rng.calls=0;\n    (void)visual;\n    // The title\'s own restore',1)])
    edit('GameSession.cpp',[
        ('#include "ReplayTextTh14.hpp"','#include "ReplayTextTh14.hpp"\n#include "ReplayRngRestoreTh14.hpp"',1),
        ('recording_seed=rng.seed;rng.calls=0;animations.script_rng.seed=u16(recording_seed);',
         'th14_record_stage_rng(rng,animations.script_rng,recording_seed);',2)])
    name='th12_web/cpp/game/ReplayRngRestoreTh14.hpp';raw=(R/'runtimes/th12'/name).read_bytes();(source/name).write_bytes(raw)
    changes.append(dict(path=name,beforeSha256=None,afterSha256=sha(raw)))
    prepared=dict(baseBuild=b.relative_to(R).as_posix(),baseBuildSha256=sha(b.read_bytes()),sourceRoot=source.as_posix(),changes=changes,
                  newHeader=name,parentCoreWasmSha256=base['wasmSha256'],rootGameplaySourcesModified=False,
                  ordinaryWorkerSubstoreSchedulingImplemented=False,oldRngOrBulletFailuresClosed=False,
                  completeGame=False,nativeEquivalent=False,preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared))


if __name__=='__main__':main()
