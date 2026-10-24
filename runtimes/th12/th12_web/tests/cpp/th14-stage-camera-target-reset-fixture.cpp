#include "../../cpp/game/Stage.hpp"
#include <cstring>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource resource,text;static u32 color=0;
static Stage stage(manager,resource,text,color,3);static u32 words[22]{};
static float number(u32 bits){float value;std::memcpy(&value,&bits,4);return value;}
API(input) void input(u32 i,u32 bits){if(i<22)words[i]=bits;}
API(reset) u32 reset(){
    SceneCamera c;Vec3* vectors[]={&c.position,&c.direction,&c.up,&c.reserved24,&c.right,&c.eye_offset,&c.target_offset};
    for(u32 i=0;i<7;++i)*vectors[i]={number(words[i*3]),number(words[i*3+1]),number(words[i*3+2])};c.fov=number(words[21]);
    StageResource file;StageInstruction stop;stop.time=0;stop.opcode=0;stop.length=8;stop.offset=0;file.instructions.push_back(stop);
    return stage.initialize(file,4,c,false);
}
API(value) u32 value(u32 i){
    const auto& c=stage.state.camera;const float v[]={c.position.x,c.position.y,c.position.z,c.direction.x,c.direction.y,c.direction.z,c.up.x,c.up.y,c.up.z,c.reserved24.x,c.reserved24.y,c.reserved24.z,c.right.x,c.right.y,c.right.z,c.eye_offset.x,c.eye_offset.y,c.eye_offset.z,c.target_offset.x,c.target_offset.y,c.target_offset.z,c.fov};
    u32 out=0;if(i<22)std::memcpy(&out,v+i,4);return out;
}
