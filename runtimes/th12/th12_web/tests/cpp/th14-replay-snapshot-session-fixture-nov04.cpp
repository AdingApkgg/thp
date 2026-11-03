// Controlled separate snapshot-copy readiness after all three RNG stores.
// Controlled resource readiness on the real GameSession/loader path.
// It supplies no native RNG words or per-frame game state.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {
struct RngStepSessionEffects final:StageResourceEffects {
    StageResourceEffects* next=nullptr;u32 target=0,count=0,first=0,second=0;
    bool early_resources=false,invalid=false,fail_snapshot=false;u32 rows[3][12]{};
    mutable u32 snapshot_first=0,snapshot_ready=0,snapshot_polls=0,snapshot_waits=0;mutable bool snapshot_invalid=false;
    std::unique_ptr<ReplayRngRestoreScopeTh14> observation;
    bool prepare(StageResources& s)override{return next->prepare(s);}
    bool core_ready()const override{return next->core_ready();}
    bool stage_ready()const override{return next->stage_ready();}
    bool defer_initial_stage_decode()const override{return next->defer_initial_stage_decode();}
    bool begin_stage_worker_wait(bool initial)override{return next->begin_stage_worker_wait(initial);}
    bool stage_worker_wait_ready()const override{return next->stage_worker_wait_ready();}
    bool draw_startup_loading()override{return next->draw_startup_loading();}
    bool defer_ending_loading()const override{return next->defer_ending_loading();}
    bool begin_ending_loading()override{return next->begin_ending_loading();}
    void finish_ending_loading()override{next->finish_ending_loading();}
    DialogueEffects* dialogue_text_device()override{return next->dialogue_text_device();}
    void release(StageResources& s)override{next->release(s);}
    bool prepare_animation(AnmResource& a)override{return next->prepare_animation(a);}
    bool prepare_manual_image(AnmResource& a,u32 i,const u8* p,u32 n)override{return next->prepare_manual_image(a,i,p,n);}
    void release_animation(AnmResource& a)override{next->release_animation(a);}
    bool read_replay(const std::string& name,std::vector<u8>& out)override{return next->read_replay(name,out);}
    const std::string& last_error()const override{return next->last_error();}
    DecodeResult decode_stage_phase(GameResources& r,StageResources& s,Phase p,u32 c)override{
        if(s.stage_number==target&&(count!=3||!snapshot_ready))early_resources=true;
        return next->decode_stage_phase(r,s,p,c);
    }
    void cancel_stage_decode(StageResources& s)override{next->cancel_stage_decode(s);}
    bool prepare_stage_phase(StageResources& s,Phase p)override{
        if(s.stage_number==target&&(count!=3||!snapshot_ready))early_resources=true;
        return next->prepare_stage_phase(s,p);
    }
    bool stage_phase_ready(Phase p)const override{return next->stage_phase_ready(p);}
    void cancel_stage_phases(StageResources& s,u32 mask)override{next->cancel_stage_phases(s,mask);}
    void finish_stage_phases(StageResources& s,u32 mask)override{next->finish_stage_phases(s,mask);}
    ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14 point)const override{
        using Point=ReplayRngRestorePointTh14;using Result=ReplayRngRestoreResultTh14;
        if(session.state.stage!=target)return next->stage_rng_store_readiness(point);
        if(point==Point::GameplaySeedStored)return Result::Ready;
        if(point==Point::ScriptSeedStored){
            if(!first||public_player_observations<first+2)return Result::Waiting;
            return Result::Ready;
        }
        if(point==Point::GameplayCounterCleared)return second&&public_player_observations>=second+2?Result::Ready:Result::Waiting;
        return Result::Failed;
    }
    ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const override{
        using Result=ReplayRngRestoreResultTh14;
        if(session.state.stage!=target)return next->stage_replay_snapshot_readiness();
        ++snapshot_polls;
        if(count!=3||!session.battle||session.battle->pending_stage!=target||
           !session.battle->stage_initialization_started||session.battle->stage_initialization_finished){snapshot_invalid=true;return Result::Failed;}
        if(!snapshot_first)snapshot_first=public_player_observations;
        if(public_player_observations<snapshot_first+2){++snapshot_waits;return Result::Waiting;}
        if(fail_snapshot)return Result::Failed;
        snapshot_ready=public_player_observations;return Result::Ready;
    }
    void observed(ReplayRngRestorePointTh14 point,Rng& gameplay,Rng* script){
        if(session.state.stage!=target)return;
        if(count>=3||!script||!session.battle){invalid=true;return;}
        const auto& b=*session.battle;
        const u32 data[]={u32(point),public_player_observations,session.state.stage,b.pending_stage,
            gameplay.seed,gameplay.calls,script->seed,script->calls,b.replay_entry.seed,
            u32(b.stage_loader.phase),u32(b.stage_initialization_started),u32(b.stage_initialization_finished)};
        for(u32 i=0;i<12;++i)rows[count][i]=data[i];++count;
        if(point==ReplayRngRestorePointTh14::GameplaySeedStored)first=public_player_observations;
        if(point==ReplayRngRestorePointTh14::ScriptSeedStored)second=public_player_observations;
    }
} rng_step_session;
}
API(step_rng_session_inject_failure) u32 step_rng_session_inject_failure(u32 enabled){
    if(rng_step_session.next||enabled>1)return 0;rng_step_session.fail_snapshot=enabled!=0;return 1;
}
API(step_rng_session_install) u32 step_rng_session_install(u32 stage){
    auto& s=rng_step_session;
    if(s.next||stage<2||stage>6||!session.resources.effects||!session.battle||public_player_observations!=1)return 0;
    s.next=session.resources.effects;s.target=stage;session.resources.effects=&s;
    s.observation=std::make_unique<ReplayRngRestoreScopeTh14>(session.animations.visual_rng,&s,
        [](void* owner,ReplayRngRestorePointTh14 point,Rng& game,Rng* script){static_cast<RngStepSessionEffects*>(owner)->observed(point,game,script);});
    return 1;
}
API(step_rng_session_value) u32 step_rng_session_value(u32 row,u32 field){
    auto& s=rng_step_session;
    if(row==4){switch(field){case 0:return s.snapshot_first;case 1:return s.snapshot_ready;case 2:return s.snapshot_polls;
        case 3:return s.snapshot_waits;case 4:return s.snapshot_invalid;default:return ~0u;}}
    if(row==3){switch(field){case 0:return s.count;case 1:return s.early_resources;case 2:return s.invalid;
        case 3:return session.battle&&session.battle->stage_initialization_finished;
        case 4:return session.battle?session.battle->pending_stage:~0u;default:return ~0u;}}
    return row<s.count&&field<12?s.rows[row][field]:~0u;
}
API(step_rng_session_finish) u32 step_rng_session_finish(){
    auto& s=rng_step_session;
    if(session.resources.effects!=&s)return 0;
    s.observation.reset();session.resources.effects=s.next;
    return !ReplayRngRestoreScopeTh14::active&&!s.early_resources&&!s.invalid&&!s.snapshot_invalid&&s.count==3&&s.snapshot_ready>=s.snapshot_first+2;
}
API(step_rng_session_failure_value) u32 step_rng_session_failure_value(u32 field){
    switch(field){case 0:return !session.error.empty();case 1:return session.battle&&!session.battle->error.empty();
        case 2:return session.battle&&session.battle->stage_loader.phase==prototype::LoadPhase::Failed;
        case 3:return session.battle&&session.battle->stage_initialization_finished;default:return ~0u;}
}
API(step_rng_session_abort) u32 step_rng_session_abort(){
    auto& s=rng_step_session;if(session.resources.effects!=&s)return 0;
    s.observation.reset();session.resources.effects=s.next;return !ReplayRngRestoreScopeTh14::active;
}
