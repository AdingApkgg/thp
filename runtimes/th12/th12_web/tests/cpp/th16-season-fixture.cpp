#include "../../cpp/game/SeasonTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16SeasonState state;static AnmVm bar,levels,child1,child2;static i32 active;
struct Services final:Th16SeasonGaugeServices{
    std::vector<u32> events;
    bool children(AnmVm&,bool visible)override{for(auto* vm:{&child1,&child2})if(visible)vm->flags|=2;else vm->flags&=~2u;return true;}
    bool interrupt(AnmVm&,i32)override{return true;}
    bool update(AnmVm& vm)override{events.insert(events.end(),{0,u32(&vm==&levels),u32(vm.pending_interrupt)});return true;}
} services;
API(collect) i32 collect(i32 count,i32 maximum){state={};state.count=count;state.maximum=maximum;return state.collect();}
API(count) i32 count(){return state.count;}
API(progress) u32 progress(){return float_bits(state.progress());}
API(gauge) i32 gauge(i32 count,i32 maximum,i32 previous,u32 flags){state={};state.count=count;state.maximum=maximum;active=previous;bar={};levels={};child1={};child2={};bar.flags=levels.flags=child1.flags=child2.flags=flags;bar.th13_native_flags=flags&~7u;bar.pending_interrupt=levels.pending_interrupt=99;services.events.clear();return season_th16_gauge(state,active,bar,levels,services);}
API(value) u32 value(u32 n){const u32 v[]={float_bits(bar.sprite_size.x),(bar.th13_native_flags&~7u)|(bar.flags&7u),levels.flags,child1.flags,child2.flags,u32(bar.pending_interrupt),u32(levels.pending_interrupt),u32(active)};return v[n];}
API(event_count) u32 event_count(){return services.events.size();}
API(event) u32 event(u32 n){return services.events[n];}
static i32 point,amount;static float energy;
API(reward) void reward(i32 kind,i32 p,i32 maximum,float e){point=p;energy=e;amount=item_th16_cancel_reward(kind,point,maximum,energy);}
API(reward_word) u32 reward_word(u32 n){const u32 v[]={u32(point),float_bits(energy),u32(amount)};return v[n];}
