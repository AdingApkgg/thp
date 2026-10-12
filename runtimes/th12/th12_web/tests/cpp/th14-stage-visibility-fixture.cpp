#include "../../cpp/game/Stage.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(project) const Vec3* project(const float* a,const float* point){
 static Vec3 result;SceneCamera camera;std::memcpy(camera.view.m,a+15,64);std::memcpy(camera.projection.m,a+31,64);
 camera.viewport={u32(a[47]),u32(a[48]),u32(a[49]),u32(a[50]),a[51],a[52]};Matrix4 world;world.identity();world.m[12]=a[6];world.m[13]=a[7];world.m[14]=a[8];
 result=GraphicsMath::project({point[0],point[1],point[2]},camera.viewport,camera.projection,camera.view,world);return &result;
}
API(visible) u32 visible(const float* a){
 StageObject object;object.position={a[0],a[1],a[2]};object.size={a[3],a[4],a[5]};
 SceneCamera camera;camera.position={a[9],a[10],a[11]};camera.eye_offset={a[12],a[13],a[14]};
 std::memcpy(camera.view.m,a+15,64);std::memcpy(camera.projection.m,a+31,64);
 camera.viewport={u32(a[47]),u32(a[48]),u32(a[49]),u32(a[50]),a[51],a[52]};
 return stage_visible(object,{a[6],a[7],a[8]},camera,a[53]);
}
