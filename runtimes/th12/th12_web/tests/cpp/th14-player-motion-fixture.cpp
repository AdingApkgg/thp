#include "../../cpp/game/PlayerMotion.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;static AnmResource file;static std::vector<AnmVm*> vms;
struct World:PlayerMotionWorld{u32 create_focus()override{return 0;}};static World world;static PlayerMotion motion(file,file,animations,world);
API(begin) i32 begin(u32 held,i32 env,i32 transition,u32 variant,i32 previous,float rate,i32 count,i32 active){
 animations.clear();vms.clear();animations.rate=rate;file.scripts.resize(28);
 for(auto& script:file.scripts){script.bytes.resize(16);const AnmInstruction idle{i16(anm_canonical_opcode(2)),8,0,0},end{-1,8,0,0};std::memcpy(script.bytes.data(),&idle,8);std::memcpy(script.bytes.data()+8,&end,8);}
 for(u32 i=0;i<17;++i){auto* vm=animations.create(file,0,7,14);if(!vm)return -1;vm->position={91,-72,33};vm->extra_scale={.75,1.25};vm->pending_interrupt=77;vm->flags&=~8u;vms.push_back(vm);}
 motion.state={};motion.options={};auto& s=motion.state;const i32 x[]={-321,-23560,23560},y[]={50319,4000,55350},flags[]={0,0x12,0x10},clocks[]={0,29,31},lerp[]={29,30,67};const float factor[]={1,.5,1.5},shift_x[]={0,.125,1.25},shift_y[]={0,-.25,-.875};
 s.x=x[variant];s.y=y[variant];s.position.z=5.25;s.transition_timer=transition;s.normal_speed=576;s.focus_speed=256;s.normal_diagonal=407;s.focus_diagonal=181;s.previous_dx=previous;s.previous_dy=101;s.flags=flags[variant]&2?8u:0u;s.th14_scale_flags=flags[variant];s.option_lerp=lerp[variant];s.recall_timer=clocks[variant];s.option_count=count;motion.focus_animation=vms[0]->id;
 s.delta.z=7.25;s.last_delta={11.25,12.5,13.75};s.th14_movement_factor=factor[variant];s.th14_scale_factor=2.25;s.th14_bomb_shift={shift_x[variant],shift_y[variant],0};
 for(u32 i=0;i<66;++i)s.th14_history[i/2][i%2]=signed_bits(0x10203040+i*101);
 for(i32 n=0;n<8;++n){auto& o=motion.options[n];o.state=n<active?2:0;o.target_x=123;o.target_y=456;o.x=-300+n*53;o.y=50000+n*97;o.normal_x=-2048+n*512;o.normal_y=-1024+n*256;o.focus_x=-512+n*128;o.focus_y=-3072+n*384;o.animation=vms[1+n*2]->id;o.auxiliary=vms[2+n*2]->id;o.snap=n%2;}
 motion.body.script_index=0;PlayerMotionInput input;input.held=held;input.enemy_manager=env>0;input.enemies=env==2;return motion.update(input)?1:motion.last_error;
}
API(value) u32 value(u32 n){const auto& s=motion.state;const u32 a[]={u32(s.direction),u32(s.weapon_mode),u32(s.option_lerp),u32(s.previous_dx),u32(s.previous_dy),float_bits(s.delta.x),float_bits(s.delta.y),float_bits(s.delta.z),float_bits(s.last_delta.x),float_bits(s.last_delta.y),float_bits(s.last_delta.z),u32(s.dx),u32(s.dy),u32(s.x),u32(s.y),float_bits(s.position.x),float_bits(s.position.y),float_bits(s.position.z),u32(s.recall_timer),u32(s.option_count)};return a[n];}
API(history) u32 history(u32 n){return u32(motion.state.th14_history[n/2][n%2]);}
API(option) u32 option(u32 n,u32 k){const auto& o=motion.options[n];const u32 a[]={u32(o.state),u32(o.target_x),u32(o.target_y),u32(o.x),u32(o.y),u32(o.snap)};return a[k];}
API(focus) u32 focus(){return bool(motion.focus_animation);}
API(body_script) i32 body_script(){return motion.body.script_index;}
API(animation) u32 animation(u32 n,u32 k){const auto& vm=*vms[n];const u32 a[]={float_bits(vm.position.x),float_bits(vm.position.y),float_bits(vm.position.z),float_bits(vm.extra_scale.x),float_bits(vm.extra_scale.y),u32(vm.pending_interrupt),vm.flags&8};return a[k];}
