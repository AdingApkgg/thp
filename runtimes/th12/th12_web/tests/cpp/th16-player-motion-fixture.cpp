#include "../../cpp/game/PlayerMotion.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;static AnmResource file;static std::vector<AnmVm*> vms;static std::vector<u32> effects;static i32 old_script;
static AnmVm* create(i32 script){auto* vm=animations.create(file,script,8,14);if(vm){vm->position={91,-72,33};vm->extra_scale={.75,1.25};vm->flags&=~8u;vm->pending_interrupt=77;vms.push_back(vm);}return vm;}
struct World:PlayerMotionWorld{u32 create_movement_effect(i32 script)override{effects.push_back(script);auto* vm=create(script);return vm?vm->id:0;}};static World world;static PlayerMotion motion(file,file,animations,world,9,7);
API(begin) i32 begin(u32 held,i32 env,i32 transition,u32 seed,i32 previous,float rate,i32 charge){
 animations.clear();vms.clear();effects.clear();animations.rate=rate;file.scripts.resize(28);
 for(auto& script:file.scripts){script.bytes.resize(16);const AnmInstruction idle{i16(anm_canonical_opcode(2)),8,0,0},end{-1,8,0,0};std::memcpy(script.bytes.data(),&idle,8);std::memcpy(script.bytes.data()+8,&end,8);}
 auto* focus=create(0);auto* charge_vm=create(0);if(!focus||!charge_vm)return -1;
 motion.state={};motion.options={};auto& s=motion.state;const i32 x[]={-321,-23560,23560},y[]={50319,4000,55350},flags[]={0,0x12,0x10},clocks[]={0,29,31};const float factor[]={1,.5,1.5},shift_x[]={0,.125,1.25},shift_y[]={0,-.25,-.875};
 s.x=x[seed];s.y=y[seed];s.position.z=5.25;s.transition_timer=transition;s.normal_speed=576;s.focus_speed=256;s.normal_diagonal=407;s.focus_diagonal=181;s.previous_dx=previous;s.previous_dy=101;s.flags=flags[seed];s.option_lerp=67;s.recall_timer=clocks[seed];s.option_count=4;motion.th16_season_count=6;
 motion.focus_animation=seed==1?focus->id:seed==2?0x7fffffffu:0;s.th16_charge_animation=seed==2?charge_vm->id:0;s.th16_charge_timer.set(charge,&animations.rate);s.th16_charge_timer.previous=23;
 s.delta.z=7.25;s.last_delta={11.25,12.5,13.75};s.th16_speed_multiplier=factor[seed];s.th16_scale_factor=2.25;s.th16_displacement={shift_x[seed],shift_y[seed],0};
 motion.body.script_index=0;old_script=0;PlayerMotionInput input;input.held=held;input.enemy_manager=env>0;input.enemies=env==2;return motion.update(input)?1:motion.last_error;
}
API(value) u32 value(u32 n){const auto& s=motion.state;const auto& t=s.th16_charge_timer;const u32 a[]={u32(s.direction),u32(s.focused),u32(s.option_lerp),u32(s.previous_dx),u32(s.previous_dy),float_bits(s.delta.x),float_bits(s.delta.y),float_bits(s.delta.z),float_bits(s.last_delta.x),float_bits(s.last_delta.y),float_bits(s.last_delta.z),u32(s.dx),u32(s.dy),u32(s.x),u32(s.y),float_bits(s.position.x),float_bits(s.position.y),float_bits(s.position.z),u32(s.recall_timer),u32(s.option_count),u32(motion.th16_season_count),u32(t.previous),u32(t.current),float_bits(t.fractional)};return a[n];}
API(handle) u32 handle(u32 n){return bool(n?motion.state.th16_charge_animation:motion.focus_animation);}
API(animation_count) u32 animation_count(){return vms.size();}
API(animation) u32 animation(u32 n,u32 k){const auto& vm=*vms[n];const u32 a[]={float_bits(vm.position.x),float_bits(vm.position.y),float_bits(vm.position.z),float_bits(vm.extra_scale.x),float_bits(vm.extra_scale.y),u32(vm.pending_interrupt),vm.flags&8};return a[k];}
API(body_script) i32 body_script(){return motion.body.script_index;}
API(effect_count) u32 effect_count(){return effects.size();}
API(effect) u32 effect(u32 n){return effects[n];}
