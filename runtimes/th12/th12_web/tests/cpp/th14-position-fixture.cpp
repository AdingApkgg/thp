#include "../../cpp/game/AnmGeometry.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm nodes[3]{};
static Vec3 result[4]{};
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(u32 depth,const float* vectors,const u32* flags,float display_scale,const i32* origins,u32 mode,u32 anchor,u32 quad){
    for(u32 i=0;i<3;++i){
        auto& vm=nodes[i];vm={};vm.initialize();vm.flags2=flags[i];vm.parent=i<depth?&nodes[i+1]:nullptr;
        const auto* data=vectors+i*20;
        std::memcpy(&vm.position,data,12);std::memcpy(&vm.script_position,data+3,12);std::memcpy(&vm.child_position,data+6,12);
        std::memcpy(&vm.rotation,data+9,12);std::memcpy(&vm.sprite_size,data+12,8);std::memcpy(&vm.pivot,data+14,8);
        std::memcpy(&vm.scale,data+16,8);std::memcpy(&vm.extra_scale,data+18,8);
        vm.set_drawing_mode(mode);vm.flags|=(anchor%3)<<18|(anchor/3)<<20;
    }
    const AnmRenderSpace space{display_scale,{float(origins[0]),float(origins[1])},{float(origins[2]),float(origins[3])}};
    if(quad)return anm_quad_positions(nodes[0],result,space)?0:-1;
    result[0]=nodes[0].render_position(space);return 0;
}
API(value) float value(u32 i){const auto& p=result[i/3];return i%3==0?p.x:i%3==1?p.y:p.z;}
