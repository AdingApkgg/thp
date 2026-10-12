#include "../../cpp/game/PlayerFrame.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
#include <vector>
using namespace th11;
namespace {
struct World:PlayerFrameWorld {
    std::vector<u32> requests;
    bool spawn_item(i32 type,Vec3 p,u32 color,float angle,float speed)override{
        if(color!=0xffffff)return false;
        requests.insert(requests.end(),{u32(type),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed),0});
        return true;
    }
} world;
GameEconomy economy;
}
extern "C" {
__attribute__((export_name("run"))) u32 run(i32 power,i32 step,i32 lives,u32 x,u32 y,u32 z){
    economy.power=power;economy.power_step=step;economy.lives=lives;world.requests.clear();
    return player_th14_death_drops(economy,{float_bits(x),float_bits(y),float_bits(z)},world);
}
__attribute__((export_name("power"))) u32 power(){return u32(economy.power);}
__attribute__((export_name("count"))) u32 count(){return world.requests.size();}
__attribute__((export_name("value"))) u32 value(u32 n){return world.requests.at(n);}
}
