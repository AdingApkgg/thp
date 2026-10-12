#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;
struct Targets final:Th16ShotTargets {
 u32 mode=0;Th16ShotTarget enemy;std::vector<std::array<u32,2>> events;
 bool present()const override{return mode!=0;}
 u32 nearest(Vec3,float radius)override{events.push_back({1,float_bits(radius)});return mode==1?0:7;}
 bool valid(u32 id)override{events.push_back({2,id});return mode!=3;}
 Th16ShotTarget target(u32 id)override{events.push_back({3,id});return enemy;}
} targets;
API(begin) void begin(i32 state,u32 target,i32 age,float speed,float angle,float x,float y,u32 mode,u32 flags){shot={};shot.state=state;shot.target_id=target;shot.timer.current=age;shot.movement.position={7.25f,300.5f,1.25f};shot.movement.speed=speed;shot.movement.angle=angle;targets.mode=mode;targets.enemy={{x,y,0},flags};targets.events.clear();shot_th16_homing(shot,targets);}
API(value) u32 value(u32 n){const u32 values[]={shot.target_id,float_bits(shot.movement.speed),float_bits(shot.movement.angle)};return values[n];}
API(count) u32 count(){return targets.events.size();}
API(event) u32 event(u32 n,u32 k){return targets.events[n][k];}
