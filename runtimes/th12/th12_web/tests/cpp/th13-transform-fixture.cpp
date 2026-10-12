#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/AnmGeometry.hpp"
#include "../../cpp/game/AnmProjection.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm,parent;
static AnmVertex ring_vertices[128];static u32 allocated;
struct Environment:AnmEnvironment{
    bool allocate_geometry(AnmVm& v,u32 bytes)override{allocated=bytes;if(bytes>sizeof(ring_vertices))return false;std::memset(ring_vertices,0,sizeof(ring_vertices));v.geometry=ring_vertices;return true;}
    bool update_geometry(AnmVm& v)override{return anm_ring_vertices(v,ring_vertices,allocated/sizeof(AnmVertex));}
};
static Environment env;
alignas(4) static u8 code[64];
static Vec3 vertices[4];
API(begin_case) void begin_case(u32 op,u32 refs,u32 count,u32 a,u32 b,u32 c,u32 d,float x,float y){
    vm={};vm.initialize();vm.timer.set(0,&env.rate);vm.color=0xab123456;
    vm.extra_scale={1.25f,.75f};vm.texture_scale={1.5f,.5f};vm.pivot={3.25f,-5};
    vm.floats[0]=x;vm.floats[1]=y;vm.integers[0]=8;
    vm.script_position={3,5,8};vm.position={11.25f,-7.5f,10};
    std::memset(code,0,sizeof(code));auto* command=reinterpret_cast<AnmInstruction*>(code);
    command->opcode=anm_canonical_opcode(op);command->length=8+count*4;command->references=refs;
    const u32 args[]={a,b,c,d};std::memcpy(code+8,args,count*4);
    auto* next=reinterpret_cast<AnmInstruction*>(code+command->length);next->length=8;next->time=30000;
    vm.script_begin=vm.instruction=command;
}
API(tick) i32 tick(){return vm.update(env);}
API(value) float value(u32 i){
    const float values[]={vm.extra_scale.x,vm.extra_scale.y,vm.texture_scale.x,vm.texture_scale.y,vm.pivot.x,vm.pivot.y,vm.scroll_velocity.x,vm.scroll_velocity.y,float(vm.color>>24),vm.script_position.x,vm.script_position.y,vm.script_position.z,vm.position.x,vm.position.y,vm.position.z,vm.sprite_size.x,vm.sprite_size.y,float(vm.drawing_mode()),vm.uv_offset.x,vm.uv_offset.y};
    return values[i];
}
API(quad_case) i32 quad_case(u32 mode,u32 ax,u32 ay,u32 p){
    vm={};parent={};vm.initialize();parent.initialize();
    vm.flags=7|(mode<<22)|(ax<<18)|(ay<<20);vm.flags2=p==2?0x10000:0;
    vm.scale={1.5f,.625f};vm.extra_scale={.75f,1.25f};vm.sprite_size={31.5f,27.25f};vm.pivot={3.25f,-5};
    vm.script_position={3.25f,-9.5f,.125f};vm.position={127.25f,200.75f,.375f};vm.child_position={4.5f,2.25f,.25f};vm.rotation.z=.375f;
    if(p){vm.parent=&parent;parent.flags2=0x40000;parent.position={11.25f,-7.5f,10};parent.scale={.5f,2};parent.extra_scale={1.25f,.75f};parent.rotation.z=-.625f;}
    return anm_quad_positions(vm,vertices);
}
API(vertex) float vertex(u32 i){float out;std::memcpy(&out,reinterpret_cast<const u8*>(vertices)+i*4,4);return out;}
API(uv_case) void uv_case(float sx,float sy,float ox,float oy){vm={};vm.initialize();vm.texture_scale={sx,sy};vm.uv_offset={ox,oy};vm.uv[0]={.125f,.25f};vm.uv[1]={.75f,.375f};vm.uv[2]={.25f,.875f};vm.uv[3]={.875f,1};}
API(uv_value) float uv_value(u32 i){const auto value=anm_vertex_uv(vm,i/2);return i%2?value.y:value.x;}
API(ring_case) i32 ring_case(u32 op,u32 count,u32 p,u32 color_mode){
    begin_case(op,count==8,1,count==8?10000:count,0,0,0,0,0);allocated=0;
    vm.th13_native_flags=color_mode<<17;vm.flags2=p==2?0x10000:0;vm.color=0x9f123456;vm.secondary_color=0x6134abcd;
    vm.integers[0]=count;vm.integers[1]=3;vm.scale={5.5f,24.25f};vm.rotation={2.5f,0,.375f};vm.child_position={4.5f,2.25f,.25f};
    vm.uv[0]={.125f,.25f};vm.uv[1]={.75f,.375f};vm.uv_offset={.125f,-.25f};parent={};parent.initialize();
    if(p){vm.parent=&parent;parent.flags2=0x40000;parent.position={11.25f,-7.5f,10};}
    return vm.update(env);
}
API(ring_allocation) u32 ring_allocation(){return allocated;}
API(ring_value) float ring_value(u32 i,u32 field){float value;std::memcpy(&value,reinterpret_cast<const u8*>(&ring_vertices[i])+field*4,4);return value;}
API(ring_color) u32 ring_color(u32 i){return ring_vertices[i].color;}
API(motion_begin) void motion_begin(float rate,u32 independent_time,u32 camera){
    begin_case(0,0,0,0,0,0,0,0,0);vm.instruction->time=30000;env.rate=rate;vm.flags2=independent_time<<8;vm.th13_native_flags=camera<<15;
    env.camera_delta={.25f,-.75f,.125f};vm.scale_velocity={.125f,-.25f};vm.scroll_velocity={.25f,-.375f};vm.angular_velocity.z=.125f;
}
API(motion_value) float motion_value(u32 i){const float values[]={vm.position.x,vm.position.y,vm.position.z,vm.scale.x,vm.scale.y,vm.rotation.x,vm.rotation.y,vm.rotation.z,vm.uv_offset.x,vm.uv_offset.y,vm.timer.fractional,env.rate};return values[i];}
API(ribbon_begin) i32 ribbon_begin(u32 seed,float rate){
    begin_case(508,0,1,5,0,0,0,0,0);env.rate=rate;env.script_rng={u16(seed),0,0};vm.native_prefix_position={17.25f,-9.5f,.125f};return vm.update(env);
}
API(ribbon_initial) float ribbon_initial(u32 i){const auto& r=*static_cast<const AnmRibbon*>(vm.geometry);const float values[]={r.phase,vm.position.x,vm.position.y,vm.position.z,float(vm.layer)};return values[i];}
API(ribbon_value) float ribbon_value(u32 vertex,u32 field){float value;std::memcpy(&value,reinterpret_cast<const u8*>(vm.geometry)+vertex*24+field*4,4);return value;}
API(ribbon_color) u32 ribbon_color(u32 vertex){return static_cast<const AnmRibbon*>(vm.geometry)->vertices[vertex].color;}
API(ribbon_step) float ribbon_step(u32 i){float value;std::memcpy(&value,reinterpret_cast<const u8*>(vm.geometry)+0x300+i*4,4);return value;}
API(ribbon_timer) float ribbon_timer(){return static_cast<const AnmRibbon*>(vm.geometry)->timer.fractional;}
API(ribbon_rng) u32 ribbon_rng(u32 i){return i?env.script_rng.calls:env.script_rng.seed;}
