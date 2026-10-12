#include "../../cpp/game/PlayerTh16Life.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static PlayerFrameState state;static PlayerSpellState spell;static GameEconomy economy;static PlayerOption options[12];static i32 main_count,enemy_deaths,enemy_clock;static u32 events[32][3],count;static float rate=1;static bool available;
static void event(u32 kind,u32 a,u32 b=0){events[count][0]=kind;events[count][1]=a;events[count++][2]=b;}
struct Services:Th16PlayerDeathServices{
 bool effect(Vec3 p,i32 script)override{if(p.x!=-12.25f||p.y!=80.5f||p.z!=1.25f)return false;if(available)event(0,u32(script));return true;}
 bool bombs(i32 a,i32 b)override{event(2,u32(a),u32(b));return true;}
 bool lives(i32 a,i32 b)override{event(1,u32(a),u32(b));return true;}
 bool reset_body()override{event(3,0);event(4,0);return true;}
 bool interrupt(u32 id,i16 label)override{event(5,id,u32(label));return true;}
 bool enemy_death()override{enemy_deaths=wrapping_add(enemy_deaths,1);enemy_clock=0;return true;}
};
API(run_case) bool run_case(i32 lives,i32 deaths,u32 sf,i32 elapsed,bool bomb,u32 timer_flags,u32 inv_flags,bool effect_available){
 state={};spell={sf,elapsed,12345};economy={};economy.lives=lives;economy.life_fragments=0x12345;economy.th16_bombs=8;economy.th16_bomb_fragments=0x12345678;economy.th16_death_count=deaths;state.life_state=4;state.state_timer.flags=timer_flags;state.invincibility.flags=inv_flags;main_count=77;enemy_deaths=INT32_MAX;enemy_clock=123;
 for(u32 i=0;i<12;++i){options[i]={};options[i].state=20+i;options[i].animation=10+i*2;options[i].auxiliary=11+i*2;}count=0;available=effect_available;Services services;return player_th16_die(state,spell,economy,options,main_count,{-12.25f,80.5f,1.25f},bomb,&rate,services);
}
API(value) u32 value(u32 n){const auto& a=state.state_timer;const auto& b=state.invincibility;const u32 values[]={u32(state.life_state),u32(a.previous),u32(a.current),float_bits(a.fractional),a.flags,u32(b.previous),u32(b.current),float_bits(b.fractional),b.flags,u32(main_count),spell.flags,u32(spell.bonus),u32(economy.lives),u32(economy.th16_bombs),u32(economy.th16_death_count),u32(enemy_deaths),u32(enemy_clock)};return n<17?values[n]:u32(options[n-17].state);}
API(season_state) u32 season_state(u32 n){return u32(options[n+4].state);}
API(event_count) u32 event_count(){return count;}
API(event_value) u32 event_value(u32 n,u32 field){return events[n][field];}
