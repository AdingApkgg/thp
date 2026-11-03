#include "th14-replay-rng-restore-fixture-nov04.cpp"
#include "StagedLoaderPrototype.hpp"

API(restore_job_probe) u32 restore_job_probe(u32 mode,u32 game_seed,u32 script_seed,u32 seed,u32 game_calls,
    u32 script_calls,u32 choice,u32 bits,u32 locking,u32 target){
    using Result=ReplayRngRestoreResultTh14;
    for(auto& word:observed)word=0;
    Rng gameplay{u16(game_seed),0xabcd,game_calls},script{u16(script_seed),0xbeef,script_calls};
    ReplayStageState entry;entry.seed=seed;ReplayRngRestoreJobTh14 job;
    u32 count=0,main_result=0,main_calls=0;
    {
        RngBoundaryScope reads(script,gameplay,nullptr,[](void*,Rng&,RngBoundary){return true;},locking!=0);
        const u32 expected=mode==0?2:3;
        for(u32 allow=1;allow<=expected;++allow){
            const auto ready=[&](ReplayRngRestorePointTh14){return job.stores()<allow?Result::Ready:Result::Waiting;};
            const auto result=mode==2?job.record(gameplay,script,entry.seed,ready):job.playback(gameplay,&script,entry.seed,mode==0,ready);
            if(result!=(allow==expected?Result::Ready:Result::Waiting)||job.stores()!=allow)return 0;
            const u32 point=u32(job.last_point());
            const u32 words[]={point,gameplay.seed,gameplay.reserved,gameplay.calls,script.seed,script.reserved,script.calls,entry.seed};
            for(u32 i=0;i<8;++i)observed[10+count*8+i]=words[i];++count;
            if(target==point){auto& rng=choice?script:gameplay;main_result=bits==16?rng.next16():rng.next32();++main_calls;}
        }
    }
    if(!job.complete()||ReplayRngRestoreScopeTh14::active||RngBoundaryScope::active)return 0;
    const u32 words[]={gameplay.seed,gameplay.reserved,gameplay.calls,script.seed,script.reserved,script.calls,
        entry.seed,main_result,main_calls,count};
    for(u32 i=0;i<10;++i)observed[i]=words[i];return 1;
}

API(restore_job_controls) u32 restore_job_controls(){
    using Result=ReplayRngRestoreResultTh14;using Point=ReplayRngRestorePointTh14;
    Rng game{17,0xabcd,9},script{23,0xbeef,11};u32 seed=42,passed=0;
    ReplayRngRestoreJobTh14 paused;
    if(paused.playback(game,&script,seed,false,[](Point){return Result::Waiting;})==Result::Waiting&&
       paused.stores()==0&&game.seed==17&&game.calls==9&&script.seed==23)passed|=1;
    auto one=[&](Point){return paused.stores()<1?Result::Ready:Result::Waiting;};
    if(paused.playback(game,&script,seed,false,one)==Result::Waiting&&paused.stores()==1&&
       game.seed==42&&game.calls==9&&script.seed==23)passed|=2;
    Rng foreign{99,0,77};
    if(paused.playback(foreign,&script,seed,false,[](Point){return Result::Ready;})==Result::Failed&&foreign.seed==99&&foreign.calls==77)passed|=4;
    ReplayRngRestoreJobTh14 failed;
    if(failed.playback(game,&script,seed,false,[](Point){return Result::Failed;})==Result::Failed&&failed.stores()==0&&
       failed.playback(game,&script,seed,false,[](Point){return Result::Ready;})==Result::Failed)passed|=8;
    ReplayRngRestoreJobTh14 nested;bool nested_waited=true;
    auto reentrant=[&](Point){nested_waited&=nested.playback(game,&script,seed,false,[](Point){return Result::Ready;})==Result::Waiting;return Result::Ready;};
    if(nested.playback(game,&script,seed,false,reentrant)==Result::Ready&&nested.stores()==3&&nested_waited)passed|=16;
    const auto before=game.calls;
    if(nested.playback(game,&script,seed,false,[](Point){__builtin_trap();return Result::Failed;})==Result::Ready&&nested.stores()==3&&game.calls==before)passed|=32;
    return passed;
}

API(restore_loader_probe) u32 restore_loader_probe(u32 mode,u32 game_seed,u32 script_seed,u32 seed,u32 game_calls,
    u32 script_calls,u32 choice,u32 bits,u32 locking,u32 target){
    using Result=ReplayRngRestoreResultTh14;using Work=prototype::Work;
    for(auto& word:observed)word=0;
    Rng gameplay{u16(game_seed),0xabcd,game_calls},script{u16(script_seed),0xbeef,script_calls};
    ReplayStageState entry;entry.seed=seed;
    struct Actions final:prototype::StageActions {
        Rng& gameplay;Rng& script;ReplayStageState& entry;u32 mode,allow=0;
        ReplayRngRestoreJobTh14 job;u32 prefix=0,cleanup=0,hud=0,scene=0,owner=0,timeline=0;
        Actions(Rng& g,Rng& s,ReplayStageState& e,u32 m):gameplay(g),script(s),entry(e),mode(m){}
        bool retire_owner()override{return true;}
        bool enter_work_and_initialize()override{return false;}
        Work advance_work_and_initialize()override{
            if(!prefix)++prefix;
            const auto ready=[&](ReplayRngRestorePointTh14){return job.stores()<allow?Result::Ready:Result::Waiting;};
            const auto result=mode==2?job.record(gameplay,script,entry.seed,ready):job.playback(gameplay,&script,entry.seed,mode==0,ready);
            if(result==Result::Failed)return Work::Failed;
            if(result==Result::Waiting)return Work::Waiting;
            ++cleanup;return Work::Ready;
        }
        Work prepare_hud()override{++hud;return job.complete()?Work::Ready:Work::Failed;}
        Work prepare_scene()override{++scene;return job.complete()?Work::Ready:Work::Failed;}
        bool publish_empty_owner()override{++owner;return job.complete();}
        Work prepare_timeline()override{++timeline;return job.complete()?Work::Ready:Work::Failed;}
    } actions(gameplay,script,entry,mode);
    prototype::StagedLoader loader;
    if(!loader.request(actions,mode==0)||!loader.pump(actions,0,-1,0)||actions.job.stores())return 0;
    const u32 expected=mode==0?2:3;u32 count=0,main_result=0,main_calls=0;
    {
        RngBoundaryScope reads(script,gameplay,nullptr,[](void*,Rng&,RngBoundary){return true;},locking!=0);
        for(u32 allow=1;allow<=expected;++allow){
            actions.allow=allow;
            if(!loader.pump(actions,60000000+allow,-1,0)||actions.job.stores()!=allow)return 0;
            if(allow<expected&&(loader.phase!=prototype::LoadPhase::Initialize||actions.cleanup||actions.hud||actions.scene||actions.owner||actions.timeline))return 0;
            const u32 point=u32(actions.job.last_point());
            const u32 words[]={point,gameplay.seed,gameplay.reserved,gameplay.calls,script.seed,script.reserved,script.calls,entry.seed};
            for(u32 i=0;i<8;++i)observed[10+count*8+i]=words[i];++count;
            if(target==point){auto& rng=choice?script:gameplay;main_result=bits==16?rng.next16():rng.next32();++main_calls;}
        }
    }
    if(loader.phase!=prototype::LoadPhase::Ready||actions.prefix!=1||actions.cleanup!=1||actions.hud!=1||actions.scene!=1||actions.owner!=1||actions.timeline!=1)return 0;
    if(!loader.pump(actions,70000000,-1,0)||actions.cleanup!=1)return 0;
    const u32 words[]={gameplay.seed,gameplay.reserved,gameplay.calls,script.seed,script.reserved,script.calls,
        entry.seed,main_result,main_calls,count};
    for(u32 i=0;i<10;++i)observed[i]=words[i];return 1;
}
