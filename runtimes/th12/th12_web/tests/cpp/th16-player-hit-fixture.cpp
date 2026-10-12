#include "../../cpp/game/PlayerTh16Life.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static PlayerFrameState state;static PlayerSpellState spell;static u32 events[8][2],count;static float rate=1;
struct Services:Th16PlayerHitServices{
 bool sound(i32 id)override{events[count][0]=1;events[count++][1]=u32(id);return true;}
 bool effect(Vec3 p,i32 script)override{if(p.x!=-12.25f||p.y!=80.5f||p.z!=1.25f)return false;events[count][0]=2;events[count++][1]=u32(script);return true;}
 bool reset_body()override{events[count][0]=3;events[count++][1]=0;events[count][0]=4;events[count++][1]=0;return true;}
};
API(run_case) bool run_case(u32 flags,u32 sf,i32 elapsed,bool bomb,u32 timer_flags,u32 inv_flags){
 state={};spell={sf,elapsed,12345};state.life_state=1;state.state_timer.flags=timer_flags;state.invincibility.flags=inv_flags;count=0;Services services;return player_th16_hit(state,spell,{-12.25f,80.5f,1.25f},flags,bomb,&rate,services);
}
API(value) u32 value(u32 n){const auto& a=state.state_timer;const auto& b=state.invincibility;const u32 values[]={u32(state.life_state),u32(a.previous),u32(a.current),float_bits(a.fractional),a.flags,u32(b.previous),u32(b.current),float_bits(b.fractional),b.flags,spell.flags,u32(spell.bonus)};return values[n];}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 field){return events[n][field];}
