#include "../../cpp/game/PlayerTh16Life.hpp"
#include "../../cpp/game/PlayerFrame.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameEconomy economy;static u32 events[7][7],count;
struct World:PlayerFrameWorld{bool spawn_item(i32 kind,Vec3 p,u32,float angle,float speed)override{const u32 row[]={u32(kind),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed),0};std::memcpy(events[count++],row,sizeof row);return true;}};
API(run_case) bool run_case(i32 power,i32 step,float x,float y,float z){economy={};economy.power=power;economy.power_step=step;count=0;World world;return player_th16_death_drops(economy,{x,y,z},world);}
API(power) i32 power(){return economy.power;}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 field){return events[n][field];}
