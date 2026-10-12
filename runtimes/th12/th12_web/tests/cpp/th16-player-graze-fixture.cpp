#include "../../cpp/game/GameEconomy.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameEconomy economy;
struct Services final:Th16GrazeServices {
    std::vector<u32> events;
    bool effect(Vec3 p,i32 id)override{events.insert(events.end(),{0,u32(id),float_bits(p.x),float_bits(p.y),float_bits(p.z)});return true;}
    bool popup(Vec3 p,i32 v,u32 color)override{events.insert(events.end(),{1,float_bits(p.x),float_bits(p.y),float_bits(p.z),u32(v),color});return true;}
    bool sound(i32 id,float x)override{events.insert(events.end(),{2,u32(id),float_bits(x)});return true;}
    bool item(i32 id,Vec3 p,float angle,float speed,i32 force)override{events.insert(events.end(),{3,u32(id),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed),u32(force)});return true;}
} services;
API(run_case) i32 run_case(i32 graze,i32 chain,float px,float py,float pz,float cx,float cy,float cz){economy={};economy.graze=graze;economy.th16_graze_chain=chain;services.events.clear();return player_th16_graze(economy,{px,py,pz},{cx,cy,cz},services);}
API(value) u32 value(u32 n){return n?u32(economy.th16_graze_chain):u32(economy.graze);}
API(event_count) u32 event_count(){return services.events.size();}
API(event) u32 event(u32 n){return services.events[n];}
