#include "../../cpp/game/ShotManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
ShotPlayer player;Rng rng;std::vector<std::array<u32,6>> requests;
struct World:ShotWorld {
 bool th14_hit_item(i32 type,Vec3 p,float angle,float speed)override {
  requests.push_back({u32(type),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed)});return true;
 }
} world;
}
API(run) u32 run(i32 power,u32 plain,u32 focused,u32 third,u32 seed){
 player={};player.power=power*100;player.power_step=100;
 player.th14_plain_hits=plain;player.th14_focused_hits=focused;player.th14_hits_184bc=third;
 rng={u16(seed),0,123};requests.clear();return shot_th14_hit_rewards(player,rng,{240,123,.1f},world);
}
API(value) u32 value(u32 n){const u32 values[]={player.th14_plain_hits,player.th14_focused_hits,player.th14_hits_184bc,rng.seed,rng.calls,u32(requests.size()+27)};return values[n];}
API(count) u32 count(){return requests.size();}
API(request) u32 request(u32 n,u32 word){return requests[n][word];}
