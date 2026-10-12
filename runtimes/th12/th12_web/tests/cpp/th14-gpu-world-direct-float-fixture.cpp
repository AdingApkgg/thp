#include "th14-gpu-world-profiles-fixture.cpp"
extern "C" const float* gpu_diagnostic_float_pixels();
extern "C" EMSCRIPTEN_KEEPALIVE const float* gpu_world_direct_float_case(u32 profile,u32 world,u32 view,u32 projection,u32 textureTransform,u32 fog,u32 range,u32 point){
    if(!gpu_world_profile_case(profile,world,view,projection,textureTransform,fog,range,point))return nullptr;
    if(glGetError()!=GL_NO_ERROR)return nullptr;
    return gpu_diagnostic_float_pixels();
}
