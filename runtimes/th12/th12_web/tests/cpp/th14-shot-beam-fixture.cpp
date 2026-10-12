#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static ShotPlayer player;static ShotSpec spec;static Th14DamageArea area;static AnmVm vm;static Th14BeamUpdate event;static u32 cached;
API(spawn) void spawn(u32 flags,float x){shot={};area={};shot.th14_shot_flags=flags;shot.th14_beam_length=144;area.size.x=333;area.period=4;shot_th14_beam_spawn(shot,area);}
API(spawn_value) u32 spawn_value(u32 n){const u32 v[]={float_bits(shot.th14_beam_length),shot.th14_shot_flags,float_bits(area.size.x),u32(area.period)};return v[n];}
API(update) i32 update(i32 option,i32 state,float length,float angle,i32 focused,i32 firing,i32 count,u32 power_cache,i32 blocked,i32 enemy,i32 present,i32 hit,i32 last,float x,i32 ox,i32 oy){
 shot={};player={};spec={};area={};vm={};cached=power_cache;
 shot.spec=&spec;spec.option=option;spec.angle=angle;shot.animation=73;shot.state=state;shot.th14_beam_length=length;shot.hit_this_frame=hit;shot.hit_last_frame=last;shot.th14_area_flags=0x85;
 player.power=160;player.power_step=40;player.focused=focused;player.option_count=count;player.th14_dialogue_blocked=blocked;player.th14_enemy_manager=enemy;player.position.x=x;player.options[option-1].x=ox;player.options[option-1].y=oy;
 area.flags=0x85;area.size={333,12};area.position={17,19,.5};vm.flags=7;vm.sprite_size.x=23;vm.texture_scale.x=2;
 return shot_th14_beam_update(shot,player,area,present?&vm:nullptr,firing,cached,event);
}
API(value) u32 value(u32 n){const u32 v[]={float_bits(shot.movement.position.x),float_bits(shot.movement.position.y),float_bits(shot.movement.position.z),float_bits(shot.movement.angle),float_bits(shot.th14_beam_length),u32(shot.state),u32(shot.hit_this_frame),u32(shot.hit_last_frame),shot.animation,area.flags,float_bits(area.size.x),float_bits(area.position.x),float_bits(area.position.y),float_bits(area.position.z),vm.flags,float_bits(vm.sprite_size.x),float_bits(vm.texture_scale.x),cached};return v[n];}
API(event_value) i32 event_value(u32 n){const i32 v[]={event.pan_active,event.pan,event.interrupt,event.stop};return v[n];}
