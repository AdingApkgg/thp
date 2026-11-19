#include "ResourceCleanup.hpp"

namespace th143 {
namespace {
struct Memory {
    ResourceCleanupMemory& host;
    bool read(u32 p,u32& v){return host.read_enemy_memory(p,&v,4);}
    bool write(u32 p,u32 v){return host.write_enemy_memory(p,&v,4);}
    bool release_field(u32 p){u32 v;if(!read(p,v))return false;if(v&&!host.release_enemy_storage(v,true))return false;return write(p,0);}
};
}
bool cleanup_anm_resource(u32 self,const std::array<u32,2>& heads,ResourceCleanupMemory& host){
    Memory m{host};u32 source;if(!m.read(self+0x108,source))return false;
    // An unloaded resource retains any other dangling/nonzero fields.
    if(!source)return true;
    for(u32 node:heads){u32 budget=100000;
        while(node){u32 vm,next,resource;if(!budget--||!m.read(node,vm)||!m.read(node+4,next)||!m.read(vm+0x30,resource))return false;
            if(resource==self){u32 flags;if(!m.read(vm+0x1c,flags)||!m.write(vm+0x1c,flags|0x20))return false;}node=next;
        }
    }
    u32 count,table;if(!m.read(self+0x110,count)||!m.read(self+0x124,table))return false;
    if(static_cast<i32>(count)>100000)return false;
    for(i32 i=0;i<static_cast<i32>(count);++i){const u32 entry=table+u32(i)*24;u32 texture;
        if(!m.read(entry,texture))return false;
        if(texture&&(!host.release_graphics_object(texture)||!m.write(entry,0)))return false;
        if(!m.release_field(entry+4))return false;
    }
    for(u32 at:{0x124,0x11c,0x120,0x138,0x108,0x10c})if(!m.release_field(self+at))return false;
    return true;
}
bool cleanup_independent_graphics(IndependentGraphics& g,const std::array<u32,2>& heads,ResourceCleanupMemory& host){
    Memory m{host};
    for(u32& vm:g.animations){if(vm&&(!m.release_field(vm+0x5b4)||!host.release_enemy_storage(vm,false)))return false;vm=0;}
    if(g.surface&&!host.release_graphics_object(g.surface))return false;g.surface=0;
    if(g.resource&&(!cleanup_anm_resource(g.resource,heads,host)||!host.release_enemy_storage(g.resource,false)))return false;g.resource=0;
    if(g.pixels&&!host.release_enemy_storage(g.pixels,true))return false;g.pixels=0;
    g.signals&=~1u;g.active=0;return true;
}
}
