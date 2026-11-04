// Actual Session Scene construction during perspective publication.
// Only platform readiness changes; the real shipped Scene/ANM resources load.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {
u32 camera_word_bits(float v){u32 out;std::memcpy(&out,&v,4);return out;}
struct PerspectiveSessionEffects final:StageResourceEffects {
    StageResourceEffects* next=nullptr;
    u32 mode=0,cut=13,delivered=0,confirmed=0,invalid=0,callback=0,owner_stage=0;
    u32 source_right=0,incoming_right=~0u,phase_at_confirm=~0u,owner_retained=0,confirmation_word=~0u;
    u32 scene_decodes=0,waiting_polls=0,scene_prepares=0;
    bool allow_scene=false;const Stage* borrowed=nullptr;
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
        if(s.stage_number==2&&p==Phase::Scene){
            if(!allow_scene){++waiting_polls;return DecodeResult::Waiting;}
            ++scene_decodes;if(mode==2)return DecodeResult::Failed;
            return StageResourceEffects::decode_stage_phase(r,s,p,c);
        }
        return next->decode_stage_phase(r,s,p,c);
    }
    void cancel_stage_decode(StageResources& s)override{next->cancel_stage_decode(s);}
    bool prepare_stage_phase(StageResources& s,Phase p)override{
        if(s.stage_number==2&&p==Phase::Scene){++scene_prepares;return StageResourceEffects::prepare_stage_phase(s,p);}
        return next->prepare_stage_phase(s,p);
    }
    bool stage_phase_ready(Phase p)const override{return session.state.stage==2&&p==Phase::Scene?allow_scene:next->stage_phase_ready(p);}
    void cancel_stage_phases(StageResources& s,u32 mask)override{next->cancel_stage_phases(s,mask);}
    void finish_stage_phases(StageResources& s,u32 mask)override{next->finish_stage_phases(s,mask);}

    ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14 p)const override{return next->stage_rng_store_readiness(p);}
    ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const override{return next->stage_replay_snapshot_readiness();}
    bool boundary(const SceneCamera&,u32 copied){
        auto* battle=session.battle.get();if(!battle||session.state.stage!=2)return true;
        if(!battle->outgoing_stage)return true;
        const auto& owner=*battle->outgoing_stage;
        if(delivered){
            if(mode==0&&!confirmed&&copied==cut+1){
                if(borrowed!=&owner||battle->outgoing_stage.get()!=borrowed||!battle->stage){invalid=1;return false;}
                incoming_right=camera_word_bits(battle->stage->state.camera.right.x);
                phase_at_confirm=u32(battle->stage_loader.phase);owner_retained=1;confirmation_word=copied;
                if(battle->stage->state.stage_number!=2||incoming_right!=source_right||phase_at_confirm!=u32(prototype::LoadPhase::Timeline)){invalid=1;return false;}
                confirmed=1;
            }
            return true;
        }
        if(battle->stage_loader.phase!=prototype::LoadPhase::Scene||copied!=cut)return true;
        if(battle->outgoing_stage.get()!=&owner){invalid=1;return false;}
        borrowed=&owner;owner_stage=u32(owner.state.stage_number);callback=public_player_observations;
        source_right=camera_word_bits(session.compositor.world_camera.right.x);delivered=1;
        if(mode==1)return false;
        allow_scene=true;return true;
    }
} perspective_session;
}
API(perspective_session_install) u32 perspective_session_install(u32 mode,u32 cut){
    auto& s=perspective_session;
    if(s.next||mode>2||cut>4||!session.resources.effects||!session.battle||public_player_observations!=1||session.stage_load_perspective_boundary)return 0;
    s.next=session.resources.effects;s.mode=mode;s.cut=cut;session.resources.effects=&s;
    session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 copied){return perspective_session.boundary(camera,copied);};
    return 1;
}
API(perspective_session_value) u32 perspective_session_value(u32 index){
    auto& s=perspective_session;auto* b=session.battle.get();
    const u32 words[]={s.confirmed,s.delivered,s.invalid,s.callback,s.cut,s.source_right,s.incoming_right,s.owner_stage,session.state.stage,
        s.phase_at_confirm,s.scene_decodes,s.waiting_polls,s.allow_scene,s.scene_prepares,!session.error.empty(),b&&!b->error.empty(),
        b?u32(b->stage_loader.phase):~0u,b&&b->stage_initialization_finished,s.owner_retained,s.confirmation_word,b&&b->stage_loader.preparing_scene};
    return index<21?words[index]:~0u;
}
API(perspective_session_finish) u32 perspective_session_finish(){
    auto& s=perspective_session;if(session.resources.effects!=&s)return 0;
    session.resources.effects=s.next;session.stage_load_perspective_boundary={};
    return !s.invalid&&s.delivered&&(s.mode!=0||s.confirmed);
}
