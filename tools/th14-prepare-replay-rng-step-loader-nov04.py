"""Freeze resumable next-stage RNG initialization through production loader APIs."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

R=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-prepare-replay-rng-restore-nov04.py'),'--output',str(out)],check=True,capture_output=True)
    previous=(out/'prepared.json').read_bytes();(out/'parent-prepared.json').write_bytes(previous);prepared=json.loads(previous);source=Path(prepared['sourceRoot'])
    changes={row['path']:row for row in prepared['changes']}

    def replace(text,old,new,count=1):
        assert text.count(old)==count,(old,text.count(old));return text.replace(old,new)

    def body(text,marker):
        start=text.index(marker);opening=text.index('{',start);depth=0
        for at in range(opening,len(text)):
            depth+=(text[at]=='{')-(text[at]=='}')
            if depth==0:return start,at+1
        raise AssertionError(marker)

    def edit(name,transform):
        path=source/'th12_web/cpp/game'/name;raw=path.read_bytes();text=transform(raw.decode().replace('\r\n','\n'))
        ending='\r\n'if raw.count(b'\r\n')==raw.count(b'\n')and b'\r\n'in raw else'\n'
        path.write_bytes(text.replace('\n',ending).encode());key='th12_web/cpp/game/'+name
        if key not in changes:changes[key]=dict(path=key,beforeSha256=sha(raw))
        changes[key]['afterSha256']=sha(path.read_bytes())

    def replay_header(text):
        return replace(text,'    void restore(GameEconomy&,Rng&,bool first,Rng* visual=nullptr)const;',
                       '    void restore(GameEconomy&,Rng&,bool first,Rng* visual=nullptr)const;\n#if PORT_TITLE == 14\n    void restore_economy_th14(GameEconomy&)const;\n#endif')
    edit('Replay.hpp',replay_header)

    def replay(text):
        start=text.index('    (void)first;const auto value=')
        end=text.index('\n#endif',start)
        fields=text[start:end];assert fields.count('return;')==1
        fields=fields.replace('(void)first;','',1).replace('return;','',1)
        text=text[:start]+'    restore_economy_th14(e);return;'+text[end:]
        marker='void ReplayStageState::restore_position('
        return replace(text,marker,'#if PORT_TITLE == 14\nvoid ReplayStageState::restore_economy_th14(GameEconomy& e)const{\n'+fields+'\n}\n#endif\n'+marker)
    edit('Replay.cpp',replay)

    def resources(text):
        text=replace(text,'#if PORT_TITLE == 14\nclass AnmManager;',
                     '#if PORT_TITLE == 14\n#include "ReplayRngRestoreTh14.hpp"\nclass AnmManager;')
        # The include must precede namespace th11; avoid nesting the header's
        # namespace when this file is included from an external fixture.
        text=replace(text,'namespace th11 {\n#if PORT_TITLE == 14\n#include "ReplayRngRestoreTh14.hpp"',
                     '#if PORT_TITLE == 14\n#include "ReplayRngRestoreTh14.hpp"\n#endif\nnamespace th11 {\n#if PORT_TITLE == 14')
        return replace(text,'    enum class DecodeResult:u32 {Waiting,Ready,Failed};',
                       '    enum class DecodeResult:u32 {Waiting,Ready,Failed};\n    virtual ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14)const{return ReplayRngRestoreResultTh14::Ready;}')
    edit('GameSessionResources.hpp',resources)

    def loader(text):
        text=replace(text,'Ready,Aborted,Failed};','Ready,Aborted,Failed,Initialize};')
        text=replace(text,' virtual bool enter_work_and_initialize()=0;',
                     ' virtual bool enter_work_and_initialize()=0;\n virtual Work advance_work_and_initialize(){return enter_work_and_initialize()?Work::Ready:Work::Failed;}')
        text=replace(text,' bool initial_stage=false,has_sample=false;',
                     ' bool initial_stage=false,has_sample=false,initializing=false;')
        text=replace(text,'initial_stage=initial;has_sample=false;deadline=0;',
                     'initial_stage=initial;has_sample=false;initializing=false;deadline=0;')
        start,end=body(text,' bool poll_initialization(')
        method=''' bool poll_initialization(StageActions& actions,u64 now){
  if(phase==LoadPhase::Aborted||phase==LoadPhase::Failed)return false;
  if(initializing)return true;
  if(phase!=LoadPhase::WaitMinimum&&phase!=LoadPhase::Initialize)return true;
  if(has_sample&&now<last_sample){phase=LoadPhase::Failed;return false;}
  has_sample=true;last_sample=now;
  if(phase==LoadPhase::WaitMinimum){
   if(now<deadline||!actions.worker_wait_ready())return true;
   phase=LoadPhase::Initialize;
  }
  struct Guard {bool& flag;Guard(bool& v):flag(v){flag=true;}~Guard(){flag=false;}} guard(initializing);
  const auto result=actions.advance_work_and_initialize();
  if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
  if(result==Work::Ready)phase=LoadPhase::Hud;
  return true;
 }'''
        text=text[:start]+method+text[end:]
        return replace(text,'''   if(phase==LoadPhase::WaitMinimum){
    if(!poll_initialization(actions,now))return false;
    if(phase==LoadPhase::WaitMinimum)return true;
   }''','''   if(phase==LoadPhase::WaitMinimum||phase==LoadPhase::Initialize){
    if(!poll_initialization(actions,now))return false;
    if(phase==LoadPhase::WaitMinimum||phase==LoadPhase::Initialize)return true;
   }''')
    edit('StagedLoaderPrototype.hpp',loader)

    def battle_header(text):
        text=replace(text,'    std::function<bool()> next_stage_initializer;',
                     '    std::function<bool()> next_stage_initializer;\n    std::function<prototype::Work()> next_stage_initializer_step;\n    bool stage_initialization_started=false,stage_initialization_finished=false;')
        text=replace(text,'    bool next_stage(GameResources&,u32,std::function<bool()>);',
                     '    bool next_stage(GameResources&,u32,std::function<bool()>);\n    bool next_stage(GameResources&,u32,std::function<bool()>,std::function<prototype::Work()>);')
        return replace(text,'    bool initialize_stage_work();',
                       '    bool initialize_stage_work();\n    prototype::Work advance_stage_work();')
    edit('GameBattle.hpp',battle_header)

    def battle(text):
        text=replace(text,'    bool enter_work_and_initialize()override{return battle.initialize_stage_work();}',
                     '    bool enter_work_and_initialize()override{return battle.initialize_stage_work();}\n    prototype::Work advance_work_and_initialize()override{return battle.advance_stage_work();}')
        text=replace(text,'bool GameBattle::next_stage(GameResources& source,u32 number,std::function<bool()> initialize){',
                     '''bool GameBattle::next_stage(GameResources& source,u32 number,std::function<bool()> initialize){
    return next_stage(source,number,std::move(initialize),{});
}
bool GameBattle::next_stage(GameResources& source,u32 number,std::function<bool()> initialize,std::function<prototype::Work()> initialize_step){''')
        text=replace(text,'pending_stage=number;next_stage_source=&source;next_stage_initializer=std::move(initialize);',
                     'pending_stage=number;next_stage_source=&source;next_stage_initializer=std::move(initialize);\n    next_stage_initializer_step=std::move(initialize_step);stage_initialization_started=stage_initialization_finished=false;')
        start,end=body(text,'bool GameBattle::initialize_stage_work()')
        old=text[start:end]
        marker='    next_stage_initializer={};\n';assert old.count(marker)==1
        tail=old[old.index(marker)+len(marker):]
        assert tail.count('return true;')==1 and 'return false;'not in tail
        tail=tail.replace('return true;','stage_initialization_finished=true;return prototype::Work::Ready;')
        method='''bool GameBattle::initialize_stage_work(){return advance_stage_work()==prototype::Work::Ready;}
prototype::Work GameBattle::advance_stage_work(){
    if(stage_initialization_finished)return prototype::Work::Ready;
    if(!stage_initialization_started){
        if(!compositor.stage_start()){error="TH14 worker copy0 reset failed";return prototype::Work::Failed;}
        stage_initialization_started=true;
    }
    if(next_stage_initializer_step){
        const auto result=next_stage_initializer_step();
        if(result!=prototype::Work::Ready)return result;
    }else if(next_stage_initializer&&!next_stage_initializer())return prototype::Work::Failed;
    next_stage_initializer={};next_stage_initializer_step={};
'''+tail
        return text[:start]+method+text[end:]
    edit('GameBattle.cpp',battle)

    def session(text):
        marker='auto initialize=[this](){';assert text.count(marker)==2
        positions=[];at=0
        for unused in range(2):
            start,end=body(text,marker if at==0 else marker)if at==0 else (None,None)
            if at:
                offset=text.index(marker,at);relative_start,relative_end=body(text[offset:],marker);start,end=offset+relative_start,offset+relative_end
            positions.append((start,end));at=end
        template='''auto initialize=[this,restore=ReplayRngRestoreJobTh14{}]()mutable->prototype::Work {
    auto& rng=animations.visual_rng;
    const auto ready=[this](ReplayRngRestorePointTh14 point){return resources.effects?resources.effects->stage_rng_store_readiness(point):ReplayRngRestoreResultTh14::Ready;};
    const auto progress=state.replay?restore.playback(rng,&animations.script_rng,battle->replay_entry.seed,false,ready):
        restore.record(rng,animations.script_rng,recording_seed,ready);
    if(progress==ReplayRngRestoreResultTh14::Waiting)return prototype::Work::Waiting;
    if(progress==ReplayRngRestoreResultTh14::Failed){error="TH14 stage RNG restore failed";return prototype::Work::Failed;}
    if(state.replay){
        battle->replay_entry.restore_economy_th14(economy);
        battle->enemy_environment.spell_practice_id=battle->replay_entry.th14_practice_mode;
        battle->hud.score.continues=battle->replay_entry.continues;
        battle->player->state.minimum_point_value=signed_bits(battle->replay_entry.th14_globals[10]);
    }
    return prototype::Work::Ready;
}'''
        for start,end in reversed(positions):
            old=text[start:end];assert 'th14_record_stage_rng' in old and 'replay_entry.restore('in old
            indent=text[text.rfind('\n',0,start)+1:start];assert not indent.strip()
            replacement=template.replace('\n','\n'+indent);text=text[:start]+replacement+text[end:]
        return replace(text,'next_stage(*source,next,std::move(initialize))','next_stage(*source,next,{},std::move(initialize))',2)
    edit('GameSession.cpp',session)
    prepared.update(changes=list(changes.values()),resumableNextStageRngThroughProductionLoader=True,
                    defaultHostAllStoresReady=True,ordinaryBrowserIndependentSubstoreTimingAccepted=False,
                    initialReplayConstructionStillSynchronous=True,oldRngOrBulletFailuresClosed=False,
                    parentPreparerSha256=sha((R/'tools/th14-prepare-replay-rng-restore-nov04.py').read_bytes()),
                    preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared))


if __name__=='__main__':main()
