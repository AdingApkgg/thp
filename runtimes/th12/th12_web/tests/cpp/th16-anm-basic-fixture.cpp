#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm{};static AnmEnvironment env;
alignas(4) static u8 code[64];
API(run) i32 run(u32 op,i32 value,u32 child,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags=7|(child?0x100:0);
    vm.color=0xab123456;vm.secondary_color=0x78345678;vm.scale={1,-2.5};
    const i32 ints[]={-257,255,4096,13};const float floats[]={-1.25,.125,448,-99};std::memcpy(vm.integers,ints,sizeof ints);std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;
    const bool real=op==400||op==401||op==402;const u32 count=op==402?2:op==403||op==405?1:3;p->length=8+4*count;
    for(u32 i=0;i<count;++i){const i32 val=refs&(1u<<i)?i32((real?10004:10000)+i):value+i32(i*7);if(real){const float f=float(val);std::memcpy(code+8+i*4,&f,4);}else std::memcpy(code+8+i*4,&val,4);}
    auto* next=reinterpret_cast<AnmInstruction*>(code+p->length);next->time=32760;next->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(word) u32 word(u32 n){
    switch(n){case 0:return vm.color;case 1:return vm.secondary_color;case 2:return vm.flags&12;case 3:return u32(reinterpret_cast<u8*>(vm.instruction)-code);default:break;}
    const float values[]={vm.script_position.x,vm.script_position.y,vm.script_position.z,vm.child_position.x,vm.child_position.y,vm.child_position.z,vm.rotation.x,vm.rotation.y,vm.rotation.z,vm.scale.x,vm.scale.y};u32 result=0;if(n>=4&&n<15)std::memcpy(&result,values+n-4,4);return result;
}
API(run_interp) i32 run_interp(i32 duration,i32 mode,u32 child,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags=7|(child?0x100:0);
    vm.script_position={1.5,-2.75,3.25};vm.child_position={-9.5,.125,448};vm.integers[0]=duration;
    vm.floats[0]=.5;vm.floats[1]=-33.25;vm.floats[2]=1024;env.default_tangent={4.5,-5.75,6.25};
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(407);p->length=28;p->references=refs;
    const i32 args[]={refs&1?10000:duration,mode};std::memcpy(code+8,args,sizeof args);
    const float target[]={12.5,-13.25,14.75};for(u32 i=0;i<3;++i){const float f=refs&(4u<<i)?float(10004+i):target[i];std::memcpy(code+16+i*4,&f,4);}
    // Stop immediately after dispatch, before shared interpolation sampling.
    auto* stop=reinterpret_cast<AnmInstruction*>(code+28);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(interp_word) u32 interp_word(u32 n){
    const auto& v=vm.position_interpolation;u32 result=0;
    if(n<12){const float* arrays[]={v.start,v.end,v.initial_tangent,v.final_tangent};std::memcpy(&result,arrays[n/3]+n%3,4);return result;}
    switch(n){case 12:return u32(v.timer.previous);case 13:return u32(v.timer.current);case 14:std::memcpy(&result,&v.timer.fractional,4);return result;case 15:return u32(v.duration);case 16:return u32(v.mode);default:return 0;}
}
API(run_hermite) i32 run_hermite(i32 duration,u32 child,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags=7|(child?0x100:0);
    vm.script_position={1.5,-2.75,3.25};vm.child_position={-9.5,.125,448};vm.integers[0]=duration;
    const float floats[]={.5,-33.25,1024,-.0};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(420);p->length=48;p->references=refs;
    const i32 count=refs&1?10000:duration;std::memcpy(code+8,&count,4);
    const float args[]={12.5,-13.25,14.75,-15.5,16.25,-17.75,18.5,-19.25,20.75};
    for(u32 i=0;i<9;++i){const float v=refs&(2u<<i)?float(10004+i%4):args[i];std::memcpy(code+12+i*4,&v,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+48);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(run_texture) i32 run_texture(u32 op,i32 duration,i32 mode,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags=7;vm.th13_native_flags=7;
    vm.integers[0]=duration;const float floats[]={.5,-33.25,1024,-.0};std::memcpy(vm.floats,floats,sizeof floats);
    vm.texture_scale={1.5,-2.75};auto& v=vm.texture_scale_interpolation;
    v.initial_tangent[0]=9;v.initial_tangent[1]=10;v.final_tangent[0]=11;v.final_tangent[1]=12;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=op==429?16:24;p->references=refs;
    if(op==430){const i32 args[]={refs&1?10000:duration,mode};std::memcpy(code+8,args,sizeof args);}
    const float args[]={12.5,-13.25};for(u32 i=0;i<2;++i){const float f=refs&((op==429?1u:4u)<<i)?float(10004+i):args[i];std::memcpy(code+(op==429?8:16)+i*4,&f,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+p->length);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(texture_word) u32 texture_word(u32 n){
    const auto& v=vm.texture_scale_interpolation;u32 bits;
    if(n<2){const float values[]={vm.texture_scale.x,vm.texture_scale.y};std::memcpy(&bits,values+n,4);return bits;}
    if(n<10){const float* arrays[]={v.start,v.end,v.initial_tangent,v.final_tangent};std::memcpy(&bits,arrays[(n-2)/2]+(n-2)%2,4);return bits;}
    switch(n){case 10:return u32(v.timer.previous);case 11:return u32(v.timer.current);case 12:std::memcpy(&bits,&v.timer.fractional,4);return bits;case 13:return u32(v.duration);case 14:return u32(v.mode);default:return vm.th13_native_flags;}
}
static u32 interpolation_opcode;
template<class T,u32 N> static void seed_tangents(Interpolator<T,N>& v){for(u32 i=0;i<N;++i){v.initial_tangent[i]=T(9+i);v.final_tangent[i]=T(9+N+i);}}
API(run_other_interp) i32 run_other_interp(u32 op,i32 duration,i32 mode,i32 value,u32 refs){
    interpolation_opcode=op;vm={};vm.initialize();env.rate=1;env.default_tangent={};vm.timer.set(0,&env.rate);vm.flags=7;vm.th13_native_flags=0x60000;
    vm.color=0xab123456;vm.secondary_color=0x78345678;vm.rotation={1.5,-2.75,3.25};vm.scale={1,-2.5};
    for(u32 i=0;i<4;++i)vm.integers[i]=i?value+i32((i-1)*7):duration;
    for(u32 i=0;i<3;++i)vm.floats[i]=float(value+i32(i*7));
    seed_tangents(vm.color_interpolation);seed_tangents(vm.alpha_interpolation);seed_tangents(vm.rotation_interpolation);seed_tangents(vm.scale_interpolation);seed_tangents(vm.color2_interpolation);seed_tangents(vm.alpha2_interpolation);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;
    const bool real=op==410||op==412;const u32 width=op==409||op==414?1:op==412?2:3;p->length=16+width*4;
    const i32 args[]={refs&1?10000:duration,mode};std::memcpy(code+8,args,sizeof args);
    for(u32 i=0;i<width;++i){const i32 val=refs&(4u<<i)?i32((real?10004:10001)+i):value+i32(i*7);if(real){const float f=float(val);std::memcpy(code+16+i*4,&f,4);}else std::memcpy(code+16+i*4,&val,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+p->length);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
template<class T,u32 N> static u32 interpolation_word(const Interpolator<T,N>& v,u32 n){
    if(n<4*N){const T* arrays[]={v.start,v.end,v.initial_tangent,v.final_tangent};u32 result;std::memcpy(&result,arrays[n/N]+n%N,4);return result;}
    switch(n-4*N){case 0:return u32(v.timer.previous);case 1:return u32(v.timer.current);case 2:{u32 bits;std::memcpy(&bits,&v.timer.fractional,4);return bits;}case 3:return u32(v.duration);case 4:return u32(v.mode);case 5:return vm.flags&12;case 6:return (vm.th13_native_flags>>17)&3;default:return 0;}
}
API(other_interp_word) u32 other_interp_word(u32 n){switch(interpolation_opcode){case 408:return interpolation_word(vm.color_interpolation,n);case 409:return interpolation_word(vm.alpha_interpolation,n);case 410:return interpolation_word(vm.rotation_interpolation,n);case 412:return interpolation_word(vm.scale_interpolation,n);case 413:return interpolation_word(vm.color2_interpolation,n);default:return interpolation_word(vm.alpha2_interpolation,n);}}
API(run_lifecycle) i32 run_lifecycle(i32 op,u32 flags,i32 clock){
    vm={};vm.initialize();env.rate=1;vm.flags=flags;vm.timer.previous=clock-1;vm.timer.current=clock;vm.timer.fractional=float(clock)+.25f;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=op<0?-1:anm_canonical_opcode(u16(op));p->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(lifecycle_word) u32 lifecycle_word(u32 n){switch(n){case 0:return vm.flags&1;case 1:return !vm.instruction;case 2:return u32(vm.timer.previous);case 3:return u32(vm.timer.current);default:{u32 bits;std::memcpy(&bits,&vm.timer.fractional,4);return bits;}}}
API(run_velocity) i32 run_velocity(u32 op,i32 value,u32 refs,u32 flags2){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags2=flags2;
    vm.angular_velocity={1.5,-2.75,3.25};vm.scale_velocity={.25,-.125};vm.scroll_velocity={4.5,-5.75};
    const float floats[]={-1.25,.125,448,-99};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;
    const u32 width=op==415?3:op==416?2:1;p->length=8+width*4;
    for(u32 i=0;i<width;++i){const float v=refs&(1u<<i)?float(10004+i):float(value+i32(i*7));std::memcpy(code+8+i*4,&v,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+p->length);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(velocity_word) u32 velocity_word(u32 n){
    if(n==7)return vm.flags2;if(n==8)return vm.flags&12;
    const float values[]={vm.angular_velocity.x,vm.angular_velocity.y,vm.angular_velocity.z,vm.scale_velocity.x,vm.scale_velocity.y,vm.scroll_velocity.x,vm.scroll_velocity.y};u32 bits=0;if(n<7)std::memcpy(&bits,values+n,4);return bits;
}
API(run_jump) i32 run_jump(u32 offset,i32 time,u32 refs,u32 flags){
    vm={};vm.initialize();env.rate=1;vm.timer.previous=18;vm.timer.current=19;vm.timer.fractional=19.25;vm.timer.flags=flags;vm.timer.rate=&env.rate;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(200);p->length=16;p->references=refs;
    std::memcpy(code+8,&offset,4);std::memcpy(code+12,&time,4);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+offset);stop->opcode=2;stop->length=8;stop->time=-32768;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(jump_word) u32 jump_word(u32 n){switch(n){case 0:return vm.trace[1].offset;case 1:return u32(vm.timer.previous);case 2:return u32(vm.timer.current);case 3:{u32 bits;std::memcpy(&bits,&vm.timer.fractional,4);return bits;}default:return vm.timer.flags;}}
API(run_counter) i32 run_counter(i32 value,u32 refs,i32 time){
    vm={};vm.initialize();env.rate=1;vm.timer.previous=18;vm.timer.current=19;vm.timer.fractional=19.25;vm.timer.flags=1;vm.timer.rate=&env.rate;vm.integers[0]=value;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(201);p->length=20;p->references=refs;
    const i32 args[]={refs&1?10000:value,40,time};std::memcpy(code+8,args,sizeof args);
    for(u32 off:{20u,40u}){auto* stop=reinterpret_cast<AnmInstruction*>(code+off);stop->opcode=2;stop->length=8;stop->time=-32768;}
    vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(counter_word) u32 counter_word(u32 n){switch(n){case 0:return u32(vm.integers[0]);case 1:{u32 bits;std::memcpy(&bits,code+8,4);return bits;}case 2:return vm.trace[1].offset;case 3:return u32(vm.timer.previous);case 4:return u32(vm.timer.current);default:{u32 bits;std::memcpy(&bits,&vm.timer.fractional,4);return bits;}}}

API(run_polar_interp) i32 run_polar_interp(i32 duration,i32 mode,u32 child,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags=7|(child?0x100:0);vm.script_position={1.5,-2.75,3.25};vm.child_position={-9.5,.125,448};vm.integers[0]=duration;
    const float floats[]={.5,-33.25,1024,-.0};std::memcpy(vm.floats,floats,sizeof floats);env.default_tangent={4.5,-5.75,6.25};
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(433);p->length=24;p->references=refs;
    const i32 args[]={refs&1?10000:duration,mode};std::memcpy(code+8,args,sizeof args);const float args2[]={refs&4?10004.f:-.75f,refs&8?10005.f:33.25f};std::memcpy(code+16,args2,sizeof args2);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+24);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
