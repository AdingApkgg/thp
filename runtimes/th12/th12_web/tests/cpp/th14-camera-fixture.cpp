#include "../../cpp/game/Stage.hpp"
#include <cstdlib>
using namespace th11;
static StageState state;
static StageResource resource;
static float rate=1;
struct World:StageScriptWorld{
    bool stage_animation(AnmVm&,i32)override{return true;}
    bool stage_deformation(i32)override{return true;}
    void stage_color(u32)override{}
} world;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(begin) i32 begin(const u8* p,u32 n,float speed){
    state={};rate=speed;state.camera.position={0,0,-600};state.camera.direction={0,300,600};state.script_timer.set(0,&rate);
    std::vector<u8> bytes(0x94+n);const u32 instance=0x90,script=0x94;std::memcpy(bytes.data()+4,&instance,4);std::memcpy(bytes.data()+8,&script,4);
    bytes[0x90]=bytes[0x91]=255;std::memcpy(bytes.data()+0x94,p,n);return resource.open(bytes.data(),bytes.size());
}
API(effect) void effect(u32 kind,i32 frame){state.camera_effect=kind;state.effect_timer.set(frame,&rate);}
API(tick) i32 tick(){state.camera.animation_delta={};return stage_script(state,resource,&rate,world);}
API(value) float value(u32 i){
    const auto& c=state.camera;const float out[]={c.position.x,c.position.y,c.position.z,c.direction.x,c.direction.y,c.direction.z,c.up.x,c.up.y,c.up.z,
        c.eye_offset.x,c.eye_offset.y,c.eye_offset.z,c.target_offset.x,c.target_offset.y,c.target_offset.z,c.animation_delta.x,c.animation_delta.y,c.animation_delta.z,c.fov,
        c.fog.near_distance,c.fog.far_distance,c.fog.channels[0],c.fog.channels[1],c.fog.channels[2],c.fog.channels[3],state.script_timer.fractional,state.effect_timer.fractional};return out[i];
}
API(integer) u32 integer(u32 i){const u32 out[]={u32(state.script_timer.current),u32(state.effect_timer.current),state.instruction_offset,state.camera.fog.color};return out[i];}
static SceneCamera view_camera;
API(view_begin) void view_begin(const float* input){
    view_camera={};std::memcpy(&view_camera.position,input,12);std::memcpy(&view_camera.direction,input+3,12);
    std::memcpy(&view_camera.up,input+6,12);std::memcpy(&view_camera.reserved24,input+9,12);std::memcpy(&view_camera.eye_offset,input+12,12);
    view_camera.target_offset={9,13,17};view_camera.fov=.625;view_camera.viewport={116,4,408,472,0,1};view_camera.perspective();
}
API(view_matches) i32 view_matches(const Vec3* input,const float* projection){
    const auto v=GraphicsMath::look_at(input[0],input[1],input[2]);const auto p=GraphicsMath::perspective(projection[0],projection[1],projection[2],projection[3]);
    return !std::memcmp(&v,&view_camera.view,sizeof v)&&!std::memcmp(&p,&view_camera.projection,sizeof p);
}
