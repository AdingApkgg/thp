"""Keep replay snapshot restoration waiting after the three completed RNG stores."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    parent=R/'artifacts/th14/stage-object-boundaries-v2-nov04';base_path=parent/'build/ordinary/observer-build.json';base_raw=base_path.read_bytes();base=json.loads(base_raw)
    old=Path(base['sourceSnapshotRoot']);source=out/'source';changes=[]
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        raw=(old/name).read_bytes();assert sha(raw)==digest;target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    def edit(name,old_text,new_text):
        path=source/'th12_web/cpp/game'/name;before=path.read_bytes();text=before.decode().replace('\r\n','\n');assert text.count(old_text)==1
        text=text.replace(old_text,new_text);ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n';after=text.replace('\n',ending).encode();path.write_bytes(after)
        changes.append(dict(path='th12_web/cpp/game/'+name,beforeSha256=sha(before),afterSha256=sha(after)))
    edit('GameSessionResources.hpp','    virtual void finish_stage_phases(StageResources&,u32){}',
        '    virtual void finish_stage_phases(StageResources&,u32){}\n    // Retail456133 begins the replay globals copy after the three RNG stores.\n    virtual ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const{return ReplayRngRestoreResultTh14::Ready;}')
    marker='''            if(progress==ReplayRngRestoreResultTh14::Failed){error="TH14 stage RNG restore failed";return prototype::Work::Failed;}
            if(state.replay){
                battle->replay_entry.restore_economy_th14(economy);'''
    edit('GameSession.cpp',marker,'''            if(progress==ReplayRngRestoreResultTh14::Failed){error="TH14 stage RNG restore failed";return prototype::Work::Failed;}
            if(state.replay){
                const auto snapshot=resources.effects?resources.effects->stage_replay_snapshot_readiness():ReplayRngRestoreResultTh14::Ready;
                if(snapshot==ReplayRngRestoreResultTh14::Waiting)return prototype::Work::Waiting;
                if(snapshot==ReplayRngRestoreResultTh14::Failed){error="TH14 replay snapshot restore failed";return prototype::Work::Failed;}
                battle->replay_entry.restore_economy_th14(economy);''')
    previous=json.loads((parent/'prepared.json').read_bytes());production={row['path']:dict(row)for row in previous['changes']}
    for row in changes:
        if row['path']in production:production[row['path']]['afterSha256']=row['afterSha256']
        else:production[row['path']]=row
    result=dict(prepared=True,baseBuild=base_path.relative_to(R).as_posix(),baseBuildSha256=sha(base_raw),sourceRoot=str(source),changes=changes,
        productionChanges=list(production.values()),parentStageObjectPreparation=(parent/'prepared.json').relative_to(R).as_posix(),
        parentPreparationSha256=sha((parent/'prepared.json').read_bytes()),sessionLayoutChanged=True,stageResourceEffectsVtableExtended=True,
        replaySnapshotCanWaitAfterAllRngStores=True,initialReplayStillSynchronous=True,replaySnapshotStillOneOperation=True,
        defaultSnapshotReadinessImmediate=True,productionIntegrated=False,rootProductionSourcesModified=False,
        oldFailureClosed=False,completeGame=False,nativeEquivalent=False,preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)


if __name__=='__main__':main()
