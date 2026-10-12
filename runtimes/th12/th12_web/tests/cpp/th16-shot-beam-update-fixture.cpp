#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;static Th16DamageSource area;static AnmVm vm;static Th16BeamEffects effects;static u32 cache;
API(begin) i32 begin(u32 seed){
 const bool season=seed&1;const i32 index=season?(seed/2)%6:(seed/2)%4;ShotSpec spec;spec.option=i8((season?101:1)+index);spec.angle=std::array<float,3>{-.75f,-1.5707963705062866f,7.f}[(seed/1024)%3];
 ShotPlayer player;player.position.x=std::array<float,4>{-200.f,-33.f,0.f,201.f}[(seed/1024)%4];player.focused=seed&32;player.power=399;player.power_step=100;player.option_count=seed&2048?0:4;player.th16_season_count=seed&2048?0:6;player.state=std::array<i32,4>{1,2,3,4}[(seed/512)%4];player.th16_dialogue=seed&256;player.th16_enemy_manager=!(seed&512);for(i32 i=0;i<12;++i)player.options[i]={-321+i*777,50319-i*333,0,0};
 shot={};shot.flags=2;shot.packed=season?0x10000:0;shot.state=std::array<i32,3>{1,2,3}[(seed/16)%3];shot.animation=77;shot.damage_source=2;shot.movement.position={7,8,9};shot.movement.angle=std::array<float,4>{-7.f,-1.5707963705062866f,spec.angle-.0005f,spec.angle+.002f}[(seed/64)%4];shot.hitbox={std::array<float,4>{0,512,510,530}[(seed/256)%4],7.5};shot.hit_this_frame=bool(seed&4);shot.hit_last_frame=bool(seed&8);cache=seed&4096?2:3;
 for(u32 n=0;n<37;++n)area.words[n]=0xa5000000+n;area.words[0]=0xabcdef07;vm={};vm.initialize();vm.flags=0x100;vm.sprite_size.x=7;vm.texture_scale.x=3;
 return shot_th16_beam_update(shot,spec,player,area,seed&128?nullptr:&vm,!(seed&1024),cache,effects);
}
API(value) u32 value(u32 n){const u32 words[]={u32(shot.state),shot.animation,float_bits(shot.movement.position.x),float_bits(shot.movement.position.y),float_bits(shot.movement.position.z),float_bits(shot.movement.angle),float_bits(shot.hitbox.x),u32(shot.hit_this_frame),u32(shot.hit_last_frame),cache,vm.flags,float_bits(vm.sprite_size.x),float_bits(vm.texture_scale.x)};return words[n];}
API(area) u32 source(u32 n){return area.words[n];}
API(count) u32 count(){return u32(effects.pan_active)+effects.count+u32(effects.stop);}
API(event) i32 event(u32 n,u32 k){if(effects.pan_active){if(!n)return k==0?1:effects.pan;--n;}if(n<effects.count)return k==0?2:effects.interrupts[n];return k==0?3:20;}
