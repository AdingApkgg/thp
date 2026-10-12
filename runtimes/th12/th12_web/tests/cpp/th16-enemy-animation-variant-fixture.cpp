#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/EnemyAnimations.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static EnemyAnimations animations(manager);static AnmResource resource;
static EnemyState enemy;static EnemyEnvironment environment;static EnemyCommandEnvironment world;
static AnmVm* old;static AnmVm* current;static u32 selected;
alignas(4) static u8 instruction[24];
API(run_case) i32 run_case(u32 slot,i32 variant,i32 base,i32 facing,u32 flags,u32 oldflags){
 manager.clear();resource={};resource.scripts.resize(256);
 const AnmInstruction code[]={AnmInstruction{i16(anm_canonical_opcode(2)),8,0,0},AnmInstruction{-1,8,0,0}};
 for(auto& script:resource.scripts){script.bytes.resize(16);std::memcpy(script.bytes.data(),code,16);}
 old=manager.create(resource,0,3,14);if(!old)return -3;old->flags2=oldflags;
 enemy={};selected=slot;enemy.animation_file=3;enemy.base_animation=base;enemy.direction=2;enemy.facing=facing;enemy.flags=flags;enemy.visual_size={11,13};
 for(u32 n=0;n<16;++n)enemy.animation_handle(n)=n==slot?old->id:100+n;
 animations.resources[3]={&resource,3};world={};world.animations=&animations;
 auto* ins=reinterpret_cast<EclInstruction*>(instruction);*ins={};ins->opcode=316;ins->length=24;
 const i32 args[]={i32(slot),variant};std::memcpy(instruction+16,args,8);EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,world);
 const auto result=services.command(c);current=manager.find(enemy.animation_handle(slot));return result;
}
API(value) u32 value(u32 n){
 if(n>=10){const auto slot=n-10;const auto id=enemy.animation_handle(slot);return slot==selected&&current&&id==current->id?1000:id;}
 i32 script=0;u32 layer=0,file=0;if(current)anm_creation_of(current->id,script,layer,file);
 const u32 values[]={u32(script),layer,file,float_bits(enemy.visual_size.x),float_bits(enemy.visual_size.y),enemy.flags,u32(enemy.direction),u32(enemy.base_animation),current?current->flags&2:0,old->flags2};return values[n];
}
