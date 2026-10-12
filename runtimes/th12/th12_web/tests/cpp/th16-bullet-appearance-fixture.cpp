#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static u32 events[16][6],count;static float rate=1;
struct Appearance:Th16BulletAppearanceServices{
 void event(u32 kind,i32 script=0){const u32 words[]={kind,u32(script),b.flags,u32(u16(b.sprite))|(u32(u16(b.color))<<16),float_bits(b.hitbox.x),u32(b.draw_group)};std::memcpy(events[count++],words,sizeof words);}
 bool reset_primary()override{event(0);return true;}
 bool bind_primary(i32 script)override{event(1,script);return true;}
 bool reset_secondary()override{event(2);return true;}
 bool interrupt_primary()override{b.vm.interrupt(2);return true;}
};
struct Services:Th16BulletStepServices{
 i32 collision(BulletState&)override{return -2;}i32 animation(AnmVm&)override{return -2;}
 bool change_appearance(BulletState& target,i32 type,u32 packed)override{Appearance service;return bullet_th16_change_appearance(target,type,packed,service);}
};
API(run_case) i32 run_case(i32 style,u32 packed,u32 flags,u32 flags2,u32 active,i32 index,i32 concurrent){
 b={};b.flags=flags;b.vm.flags2=flags2;b.sprite=2;b.color=0x1234;b.cancel_effect=-55;b.draw_group=9;b.extra=19;b.active_transforms=active;b.transform_index=index;b.transform_sound=-1;
 auto& t=b.th16_transforms[index];t.opcode=512;t.p=style;t.q=i32(packed);t.concurrent=concurrent;auto& next=b.th16_transforms[index+1];next.opcode=32768;next.p=37;next.concurrent=1;
 count=0;Services services;return bullet_th16_start_transforms(b,&rate,nullptr,nullptr,nullptr,&services);
}
API(value) u32 value(u32 n){const u32 values[]={b.flags,float_bits(b.hitbox.x),float_bits(b.hitbox.y),u32(u16(b.sprite))|(u32(u16(b.color))<<16),u32(b.draw_group),u32(b.cancel_effect),b.vm.flags2,u32(b.vm.pending_interrupt),b.active_transforms,u32(b.transform_index),u32(b.extra)};return values[n];}
API(event_count) u32 event_count(){return count;}
API(event_word) u32 event_word(u32 n,u32 f){return events[n][f];}
static AnmResource resource;static AnmManager animations;struct World:BulletWorld{};static World world;static BulletManager bullets(resource,animations,world,7);
API(production_case) i32 production_case(i32 style,u32 packed){
 resource={};resource.scripts.resize(322);const AnmInstruction code[]={AnmInstruction{i16(anm_canonical_opcode(2)),8,0,0},AnmInstruction{-1,8,0,0}};
 for(auto& script:resource.scripts){script.bytes.resize(16);std::memcpy(script.bytes.data(),code,16);}
 b={};b.vm.position={7,11,13};b.vm.layer=9;b.state=1;b.active_transforms=1;b.transform_index=3;b.cancel_effect=-55;
 return bullets.change_appearance(b,style,packed&0x7fff,(packed&0x8000)!=0)?0:-2;
}
API(production_word) u32 production_word(u32 n){const u32 v[]={u32(b.vm.script_index),u32(b.vm.pending_interrupt),b.vm.flags2&0xc0000,u32(b.vm.sprite_callback!=nullptr),u32(b.vm.layer),float_bits(b.vm.position.x),float_bits(b.vm.position.y),float_bits(b.vm.position.z),u32(b.state),b.active_transforms,u32(b.transform_index)};return v[n];}
