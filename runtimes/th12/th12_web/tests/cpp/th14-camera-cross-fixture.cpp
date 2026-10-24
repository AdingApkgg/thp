#include "../../cpp/game/SceneCamera.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
static u32 result[3];
extern "C" __attribute__((export_name("allocate"))) void* allocate(u32 size){return std::malloc(size);}
extern "C" __attribute__((export_name("camera_right"))) const u32* camera_right(const u32* input){
    SceneCamera camera;camera.position={0,0,-600};camera.reserved24={float_bits(input[0]),float_bits(input[1]),float_bits(input[2])};
    camera.up={float_bits(input[3]),float_bits(input[4]),float_bits(input[5])};camera.perspective();
    result[0]=float_bits(camera.right.x);result[1]=float_bits(camera.right.y);result[2]=float_bits(camera.right.z);return result;
}
