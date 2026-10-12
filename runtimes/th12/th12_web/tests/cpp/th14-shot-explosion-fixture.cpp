#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static ShotSpec spec;static ShotPlayer player;static std::array<Th14DamageArea,256> pool;static float rate;static u32 area_index;
API(other_counter) u32 other_counter(){return player.th14_plain_hits;}
API(hit) i32 hit(float angle,float r,float z,u32 tail0,u32 tail1){
 shot={};spec={};player={};pool={};rate=r;shot.spec=&spec;spec.damage=22;spec.native_tail[0]=tail0;spec.native_tail[1]=tail1;
 shot.state=1;shot.damage=19;shot.th14_area_flags=0x85;shot.th14_area_slot=31;shot.movement.position={12.25,301.125,.1f};shot.movement.velocity={-2,3,z};shot.movement.speed=8;shot.movement.angle=angle;shot.movement.radius=7;shot.movement.radial_velocity=.25f;shot.movement.ellipse_angle=.125f;shot.movement.ellipse_ratio=1.5f;shot.movement.flags=0;player.th14_focused_hits=5678;player.th14_hits_184bc=1234;
 u32 cursor=0;if(!th14_damage_circle(pool,cursor,shot.movement.position,24,1,20,spec.damage,&rate,area_index))return 0;return shot_th14_explosive_hit(shot,player,pool[area_index]);
}
API(value) u32 value(u32 n){const u32 values[]={u32(shot.state),float_bits(shot.movement.speed),shot.th14_area_flags,u32(shot.th14_area_slot<256),player.th14_focused_hits,player.th14_hits_184bc,u32(shot.damage)};return values[n];}
API(tick) void tick(){th14_damage_tick(pool[area_index]);}
API(area_value) u32 area_value(u32 n){const auto& a=pool[area_index];const auto& m=a.movement;const u32 v[]={a.flags,float_bits(a.radius),float_bits(a.growth),float_bits(a.angle),float_bits(a.angular_velocity),float_bits(a.position.x),float_bits(a.position.y),float_bits(a.position.z),float_bits(m.velocity.x),float_bits(m.velocity.y),float_bits(m.velocity.z),float_bits(m.speed),float_bits(m.angle),float_bits(m.radius),float_bits(m.radial_velocity),float_bits(m.ellipse_angle),float_bits(m.ellipse_ratio),m.flags,u32(a.timer.previous),u32(a.timer.current),float_bits(a.timer.fractional),u32(a.damage),u32(a.total),u32(a.maximum),u32(a.period),a.stamp,a.callback};return v[n];}
