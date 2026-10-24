#include "../../cpp/game/Stage.hpp"
#include <cstring>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;
static AnmResource resource,text;
static u32 color=0;
static SceneCamera camera;
static Stage stage(manager,resource,text,color,3);
static u32 inputs[9]{};
static float number(u32 bits){float value;std::memcpy(&value,&bits,4);return value;}
API(input) void input(u32 index,u32 bits){if(index<9)inputs[index]=bits;}
API(reference) u32 reference(u32 variable){
    stage.state.camera={};stage.state.camera.position={number(inputs[0]),number(inputs[1]),number(inputs[2])};
    stage.state.camera.eye_offset={number(inputs[3]),number(inputs[4]),number(inputs[5])};
    stage.state.camera.reserved24={number(inputs[6]),number(inputs[7]),number(inputs[8])};
    stage.active_camera=&camera;stage.publish_camera();
    AnmVm vm{};const float value=float(vm.float_value(number(variable),manager));
    u32 bits;std::memcpy(&bits,&value,4);return bits;
}
