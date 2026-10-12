#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/EnemyAnimations.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static EnemyAnimations animations(manager);static AnmResource resource;static EnemyState enemy;static EnemyEnvironment environment;static EnemyCommandEnvironment world;static AnmVm* vm;static u32 selected,initial_flags;
alignas(4) static u8 instruction[32];
struct SoundWorld final:EnemyFrameWorld {
 u32 id=0,x=0;bool accept=true;
 bool sound(i32 value,float position)override{id=u32(value);x=float_bits(position);return accept;}
 void clear_shot_targets(Enemy*)override{}
} sound_world;
static EclProgram program;static EnemyManager enemies(program,environment,world,sound_world);
API(sound_case) i32 sound_case(i32 id,u32 x,u32 accept){
 enemy={};std::memcpy(&enemy.current.position.x,&x,4);sound_world.accept=accept;world={};world.manager=&enemies;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* ins=reinterpret_cast<EclInstruction*>(instruction);ins->opcode=516;ins->length=20;std::memcpy(instruction+16,&id,4);EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,world);return services.command(c);
}
API(sound_value) u32 sound_value(u32 n){return n?sound_world.x:sound_world.id;}
API(run_case) i32 run_case(u32 op,i32 slot,u32 available,u32 flags,u32 a,u32 b,u32 d){
 manager.clear();resource={};resource.scripts.resize(1);resource.scripts[0].bytes.resize(16);const AnmInstruction code[]={AnmInstruction{i16(anm_canonical_opcode(2)),8,0,0},AnmInstruction{-1,8,0,0}};std::memcpy(resource.scripts[0].bytes.data(),code,16);
 vm=manager.create(resource,0,1,0);if(!vm)return -3;enemy={};selected=u32(slot);
 for(u32 n=0;n<16;++n)enemy.animation_handle(n)=selected==n&&available?vm->id:100+n;
 vm->rotation.z=.375f;vm->scale={2,-3};vm->scale_velocity={.125f,-.5f};vm->color=0x11223344;vm->secondary_color=0xaabbccdd;vm->th13_native_flags=flags;vm->flags=(flags&12)|3|(((flags>>5)&7)<<4);initial_flags=flags;
 *reinterpret_cast<EclInstruction*>(instruction)={};auto* c=reinterpret_cast<EclInstruction*>(instruction);c->opcode=u16(op);c->length=32;const u32 args[]={u32(slot),a,b,d};std::memcpy(instruction+16,args,16);EclContext context;context.instruction=c;world={};world.animations=&animations;EnemyScriptServices services(enemy,environment,world);return services.command(context);
}
API(value) u32 value(u32 n){
 if(n>=8){const u32 slot=n-8,id=enemy.animation_handle(slot);return slot==selected&&id==vm->id?100+slot:id;}
 const u32 flags=(vm->th13_native_flags&~0x1ecu)|(vm->flags&12)|(vm->blend_mode()<<5);
 const u32 v[]={float_bits(vm->rotation.z),float_bits(vm->scale.x),float_bits(vm->scale.y),float_bits(vm->scale_velocity.x),float_bits(vm->scale_velocity.y),vm->color,vm->secondary_color,flags};return v[n];
}
