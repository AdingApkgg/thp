#include "ShotManager.hpp"
#include "AnmGeometry.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static u32 input[52+371+9], output[32];
static ShtResource sht;
static AnmResource anm;
static AnmManager animations;
struct World final:ShotWorld{};
static World world;
static ShotManager manager(sht,anm,animations,world);
static float f(u32 bits){float value;std::memcpy(&value,&bits,4);return value;}
static Vec3 vec3(const u32* data,u32 offset){return {f(data[offset/4]),f(data[offset/4+1]),f(data[offset/4+2])};}
API(input_ptr) u32 input_ptr(){return u32(input);}
API(output_ptr) u32 output_ptr(){return u32(output);}
API(tick) i32 tick(float rate,u32 rotation){
    animations.clear();animations.rate=rate;
    anm.scripts.resize(1);
    // A registry entry for lookup/release only: no script update in this test.
    anm.scripts[0].bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
    auto* vm=animations.create(anm,0,9,0);if(!vm)return -1;
    const u32* s=input;const u32* v=input+52;const u32* g=v+371;
    const u32 flags=v[0x18/4];
    vm->flags=(flags&15)|(((flags>>21)&3)<<18)|(((flags>>23)&3)<<20);
    vm->th13_native_flags=flags;
    vm->set_drawing_mode((flags>>25)&31);vm->flags2=v[0x1c/4];
    vm->rotation.z=f(rotation);vm->scale={f(v[0x60/4]),f(v[0x64/4])};
    vm->extra_scale={f(v[0x68/4]),f(v[0x6c/4])};
    vm->sprite_size={f(v[0x80/4]),f(v[0x84/4])};
    vm->pivot={f(v[0x90/4]),f(v[0x94/4])};
    vm->script_position=vec3(v,0x3c);vm->position=vec3(v,0x59c);
    vm->child_position=vec3(v,0x4ec);vm->parent=nullptr;
    animations.render_space={f(g[0]),{float(i32(g[5])),float(i32(g[6]))},{float(i32(g[7])),float(i32(g[8]))}};
    Vec3 quad[4];if(!anm_quad_positions(*vm,quad,animations.render_space))return -2;
    for(u32 i=0;i<4;++i){output[i*3]=float_bits(quad[i].x);output[i*3+1]=float_bits(quad[i].y);output[i*3+2]=float_bits(quad[i].z);}
    for(u32 i=0;i<256;++i)manager.at(i)={};
    ShotSpec spec{};spec.type=0;spec.update=ShotUpdate::None;
    auto& shot=manager.at(0);shot.state=i32(s[0x98/4]);shot.spec=&spec;shot.animation=vm->id;
    shot.timer.previous=i32(s[0x18/4]);shot.timer.current=i32(s[0x1c/4]);shot.timer.fractional=f(s[0x20/4]);shot.timer.rate=&animations.rate;shot.timer.flags=s[0x28/4];
    shot.movement.position=vec3(s,0x54);shot.movement.velocity=vec3(s,0x88);
    shot.movement.speed=f(s[0x6c/4]);shot.movement.angle=f(s[0x70/4]);shot.movement.flags=s[0x94/4];
    shot.th14_shot_flags=s[0x10/4];manager.last_error=0;
    if(!manager.update())return -manager.last_error-10;
    output[12]=u32(shot.state);output[13]=u32(shot.animation!=0);
    output[14]=u32(shot.timer.previous);output[15]=u32(shot.timer.current);
    output[16]=float_bits(shot.timer.fractional);output[17]=shot.timer.flags;
    output[18]=float_bits(shot.movement.position.x);output[19]=float_bits(shot.movement.position.y);output[20]=float_bits(shot.movement.position.z);
    output[21]=float_bits(shot.movement.velocity.x);output[22]=float_bits(shot.movement.velocity.y);output[23]=float_bits(shot.movement.velocity.z);
    output[24]=float_bits(vm->position.x);output[25]=float_bits(vm->position.y);output[26]=float_bits(vm->position.z);output[27]=float_bits(vm->rotation.z);
    // The real port release marks its pooled VM for retirement; the retail
    // oracle's declared release service does not execute that pooled body.
    output[28]=vm->flags2;output[29]=u32(manager.last_error);
    return 1;
}
