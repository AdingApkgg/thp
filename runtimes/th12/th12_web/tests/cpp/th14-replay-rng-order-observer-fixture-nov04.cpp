// Read-only observation of the existing production worker initialization.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {
struct ReplayRngOrderObserver {
    static constexpr u32 capacity=16384,width=18;
    u32 rows[capacity][width]{},count=0;bool overflow=false,installed=false;
    u32 callback_first=0,callback_last=0;const AnmVm* current_vm=nullptr;
    std::function<bool(const AnmVm&)> previous;
    std::unique_ptr<ReplayRngRestoreScopeTh14> scope;
    bool selected()const{return public_player_observations>=callback_first&&public_player_observations<=callback_last;}
    void record(u32 kind,ReplayRngRestorePointTh14 point,const AnmVm* vm){
        if(!selected())return;
        if(count==capacity){overflow=true;return;}
        const auto& script=session.animations.script_rng;const auto& gameplay=session.animations.visual_rng;
        const auto* parent=vm?vm->parent:nullptr;
        const u32 values[]={kind,u32(point),public_player_observations,session.state.stage,
            script.seed,script.calls,gameplay.seed,gameplay.calls,
            vm?vm->file_index:~0u,vm?u32(vm->script_index):~0u,
            parent?parent->file_index:~0u,parent?u32(parent->script_index):~0u,
            vm&&vm->instruction&&vm->script_begin?u32(reinterpret_cast<const u8*>(vm->instruction)-reinterpret_cast<const u8*>(vm->script_begin)):~0u,
            session.battle?u32(session.battle->stage_loader.phase):~0u,
            u32(probe_clock_ns),u32(probe_clock_ns>>32),vm?vm->id:0,parent?parent->id:0};
        for(u32 i=0;i<width;++i)rows[count][i]=values[i];++count;
    }
} replay_rng_order;
}
API(replay_rng_order_install) u32 replay_rng_order_install(u32 first,u32 last){
    auto& o=replay_rng_order;
    if(o.installed||public_player_observations!=1||!first||last<first||last-first>8)return 0;
    o.installed=true;o.callback_first=first;o.callback_last=last;
    o.previous=session.animations.before_initial_update;
    session.animations.before_initial_update=[](const AnmVm& vm){
        auto& o=replay_rng_order;const auto* saved=o.current_vm;o.current_vm=&vm;
        o.record(0,ReplayRngRestorePointTh14::GameplaySeedStored,&vm);
        const bool result=!o.previous||o.previous(vm);
        o.current_vm=saved;return result;
    };
    o.scope=std::make_unique<ReplayRngRestoreScopeTh14>(session.animations.visual_rng,&o,
        [](void* owner,ReplayRngRestorePointTh14 point,Rng&,Rng*){
            auto& o=*static_cast<ReplayRngOrderObserver*>(owner);o.record(2,point,o.current_vm);
        });
    return 1;
}
API(replay_rng_order_count) u32 replay_rng_order_count(){return replay_rng_order.count;}
API(replay_rng_order_overflow) u32 replay_rng_order_overflow(){return replay_rng_order.overflow;}
API(replay_rng_order_value) u32 replay_rng_order_value(u32 row,u32 field){
    return row<replay_rng_order.count&&field<ReplayRngOrderObserver::width?replay_rng_order.rows[row][field]:~0u;
}
API(replay_rng_order_finish) u32 replay_rng_order_finish(){
    auto& o=replay_rng_order;if(!o.installed)return 0;
    o.scope.reset();session.animations.before_initial_update=o.previous;
    return !ReplayRngRestoreScopeTh14::active&&!o.current_vm&&!o.overflow;
}
