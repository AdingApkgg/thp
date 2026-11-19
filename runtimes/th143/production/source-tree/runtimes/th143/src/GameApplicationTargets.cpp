#include "GameApplicationTargets.hpp"
#include "AnmInstance.hpp"
namespace th143 {
bool GameApplicationTargets::construct(){
    if(!app.data)return false;
    for(u32 i=0;i<4;++i){auto& vm=vms[i];if(vm.token||!storage.allocate_game_storage(AnmView::bytes,vm.token))return false;vm.data.fill(storage.game_allocation_fill());anm_construct({vm.data.data()});app.put(0x1bc+i*4,vm.token);}
    return true;
}
u8* GameApplicationTargets::mapped(u32 p,u32 n){for(auto& vm:vms)if(vm.token&&p>=vm.token&&std::uint64_t(p)+n<=std::uint64_t(vm.token)+vm.data.size())return vm.data.data()+p-vm.token;return nullptr;}
bool GameApplicationTargets::read_render_memory(u32 p,void* out,u32 n){if(auto* b=mapped(p,n)){std::memcpy(out,b,n);return true;}return world.read(p,out,n);}
bool GameApplicationTargets::write_render_memory(u32 p,const void* in,u32 n){if(auto* b=mapped(p,n)){std::memcpy(b,in,n);return true;}return world.write(p,in,n);}
AnmView GameApplicationTargets::target_animation(u32 p){return {mapped(p,AnmView::bytes)};}
bool GameApplicationTargets::copy_target_template(u32 resource,i32 script,u32 p){auto* source=world.resource(resource);auto vm=target_animation(p);if(!source||!vm.data||script<0||u32(script)>=source->templates.size())return false;anm_copy_template(vm,p,{source->templates[script].data()},world.global_rate_token());return true;}
bool GameApplicationTargets::advance_target_animation(u32 p){auto vm=target_animation(p);return vm.data&&anm_step(vm,static_cast<AnmWorld&>(world))!=-2;}
bool GameApplicationTargets::target_backbuffer(u32 p,u32& out){return device.application_backbuffer(p,out);}
bool GameApplicationTargets::target_surface(u32 p,u32& out){i32 result;return textures.surface(p,0,out,result);}
bool GameApplicationTargets::release_target_surface(u32 p){return textures.images.find(p)!=textures.images.end()?textures.release(p):device.release_application_backbuffer(p);}
}
