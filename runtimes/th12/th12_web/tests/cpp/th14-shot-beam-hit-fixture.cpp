#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static ShotPlayer player;static Th14DamageArea area;static Th14BeamHit event;
API(other_counter) u32 other_counter(){return player.th14_focused_hits;}
API(hit) i32 hit(i32 kind,float angle,float distance,float across,i32 age,i32 advanced,float x,float y,float enemy_angle){
 shot={};player={};area={};shot.animation=71;shot.movement.position={12.25,301.125,.1};shot.movement.angle=angle;shot.th14_beam_length=512;shot.hit_last_frame=age&1;shot.timer.current=age;shot.timer.previous=age-advanced;
 area.size={333,12};area.damage=19;player.th14_plain_hits=0xfffffffe;Vec2 rect{24,40};return shot_th14_beam_hit(shot,player,area,{x,y,0},kind?&rect:nullptr,10,enemy_angle,event);
}
API(value) u32 value(u32 n){const u32 v[]={float_bits(shot.th14_beam_length),float_bits(area.size.x),u32(shot.hit_this_frame),u32(shot.hit_last_frame),player.th14_plain_hits,u32(event.damage),u32(event.interrupt),u32(event.effect),float_bits(event.position.x),float_bits(event.position.y),float_bits(event.position.z),float_bits(event.angle),float_bits(event.travel.x),float_bits(event.travel.y),float_bits(event.travel.z)};return v[n];}
API(edge) i32 edge(float ox,float oy,float angle,float width,float height,float x,float y,float radius,i32 age,i32 advanced){
 shot={};player={};area={};shot.animation=71;shot.movement.position={ox,oy,0};shot.movement.angle=angle;
 shot.th14_beam_length=width;shot.hit_last_frame=age&1;shot.timer.current=age;shot.timer.previous=age-advanced;
 area.size={width,height};area.damage=19;player.th14_plain_hits=0xfffffffe;
 return shot_th14_beam_hit(shot,player,area,{x,y,0},nullptr,radius,0,event);
}
