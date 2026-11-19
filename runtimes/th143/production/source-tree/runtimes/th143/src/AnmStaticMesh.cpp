#include "AnmStaticMesh.hpp"
namespace th143 {
namespace {
std::array<u8,80> quad(u32 ax,u32 ay){std::array<u8,80> out{};static constexpr float bounds[3][2]={{-128,128},{0,256},{-256,0}};
    for(u32 i=0;i<4;++i){AnmView v{out.data()+i*20};v.put(0,word(bounds[ax][i&1]));v.put(4,word(bounds[ay][i>>1]));v.put(8,0);v.put(12,word(float(i&1)));v.put(16,word(float(i>>1)));}return out;
}
}
bool initialize_anm_static_mesh(u32 manager,std::array<u8,96>& scratch,AnmRenderMemory& memory,AnmStaticMeshDevice& device,i32& status){
    const auto center=quad(0,0);if(!memory.write_render_memory(manager+0xbc81b0,center.data(),center.size()))return false;
    for(u32 i=0;i<4;++i){std::memcpy(scratch.data()+i*24,center.data()+i*20,12);std::memcpy(scratch.data()+i*24+16,center.data()+i*20+12,8);}
    u32 token,data;if(!device.create_static_mesh(720,0,0x102,1,token)||!memory.write_render_memory(manager+0xbc81ac,&token,4)||!device.lock_static_mesh(token,0,0,0,data))return false;
    for(u32 ax=0;ax<3;++ax)for(u32 ay=0;ay<3;++ay){const auto vertices=quad(ax,ay);if(!memory.write_render_memory(manager+0xbc81b0,vertices.data(),vertices.size())||!memory.write_render_memory(data+(ay*3+ax)*80,vertices.data(),vertices.size()))return false;}
    return device.unlock_static_mesh(token)&&device.bind_static_mesh(0,token,0,20,status);
}
}
