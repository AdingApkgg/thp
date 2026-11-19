#include "EnemyCleanup.hpp"

namespace th143 {
namespace {
struct Memory {
    EnemyCleanupMemory& host;
    bool read(u32 p,u32& v){return host.read_enemy_memory(p,&v,4);}
    bool write(u32 p,u32 v){return host.write_enemy_memory(p,&v,4);}
    bool release_field(u32 p){u32 v;if(!read(p,v))return false;if(v&&!host.release_enemy_storage(v,true))return false;return write(p,0);}
    bool mark(u32 vm){u32 flags;return read(vm+0x1c,flags)&&write(vm+0x1c,flags|0x20);}
    bool mark_resources(u32 resource,const std::array<u32,2>& heads){
        for(u32 node:heads){u32 budget=100000;
            while(node){u32 vm,next,binding;if(!budget--||!read(node,vm)||!read(node+4,next)||!read(vm+0x30,binding))return false;
                if(binding==resource&&!mark(vm))return false;node=next;
            }
        }return true;
    }
};
}
bool cleanup_enemy_visual(u32 handle,EnemyCleanupMemory& host){
    u32 vm;if(!host.find_enemy_visual(handle,vm))return false;if(!vm)return true;
    Memory m{host};u32 parent,child;if(!m.mark(vm)||!m.read(vm+0x588,parent))return false;if(parent)return true;
    if(!m.read(vm+0x584,child))return false;u32 budget=100000;
    while(child){u32 value,next;if(!budget--||!m.read(child,value)||!m.read(child+4,next)||!m.mark(value))return false;child=next;}
    return true;
}
bool cleanup_graphic_collection(u32 self,EnemyCleanupMemory& host){
    Memory m{host};if(!m.release_field(self+0x10)||!m.release_field(self+0x14))return false;
    u32 count,handles;if(!m.read(self,count)||!m.read(self+8,handles))return false;
    // The native loop is signed and visits count-1 handles. The final element
    // is intentionally not retired by this owner.
    const i32 last=static_cast<i32>(count-1);if(last>100000)return false;
    for(i32 i=0;i<last;++i){u32 handle;if(!m.read(handles+u32(i)*4,handle)||!cleanup_enemy_visual(handle,host)||!m.write(handles+u32(i)*4,0))return false;}
    return m.release_field(self+8)&&m.release_field(self+12);
}
bool cleanup_ecl_owner(u32 self,EnemyCleanupMemory& host){
    Memory m{host};if(!m.write(self,0x4c5664))return false;u32 node;if(!m.read(self+0x11d4,node))return false;u32 budget=100000;
    while(node){u32 vm,next;if(!budget--||!m.read(node,vm)||!m.read(node+4,next)||!host.release_enemy_storage(vm,false)||!host.release_enemy_storage(node,false))return false;node=next;}
    // Destruction leaves these links dangling in the original object.
    return true;
}
bool cleanup_enemy_actor(u32 self,u32 manager,EnemyCleanupMemory& host,bool release_self){
    Memory m{host};u32 head,tail,next,previous;
    if(!m.write(self,0x4c563c)||!m.read(manager+0xd0,head)||!m.read(manager+0xd4,tail)||!m.read(self+0x1580,next)||!m.read(self+0x1584,previous))return false;
    const u32 node=self+0x157c;
    if(head==node&&!m.write(manager+0xd0,next))return false;
    if(tail==node&&!m.write(manager+0xd4,previous))return false;
    if(next&&!m.write(next+8,previous))return false;
    if(previous&&!m.write(previous+4,next))return false;
    u32 count;if(!m.write(self+0x1580,0)||!m.write(self+0x1584,0)||!m.read(manager+0xd8,count)||!m.write(manager+0xd8,count-1))return false;
    u32 flags;if(!m.read(self+0x52f0,flags))return false;
    if(flags&0x800000){u32 slot;if(!m.read(self+0x5300,slot)||!m.write(manager+0x5c+slot*4,0))return false;}
    for(u32 i=0;i<24;++i){const u32 p=self+0x1314+i*4;u32 handle;if(!m.read(p,handle)||!cleanup_enemy_visual(handle,host)||!m.write(p,0))return false;}
    u32 extra;if(!m.read(self+0x53ac,extra))return false;
    if(extra&&(!cleanup_graphic_collection(extra,host)||!host.release_enemy_storage(extra,false)))return false;
    if(!m.write(self+0x53ac,0)||!cleanup_ecl_owner(self,host))return false;
    return !release_self||host.release_enemy_storage(self,false);
}
bool reset_enemies(u32 manager,const std::array<u32,6>& resources,const std::array<u32,2>& heads,EnemyCleanupMemory& host){
    Memory m{host};for(u32 resource:resources)if(!m.mark_resources(resource,heads))return false;
    u32 node;if(!m.read(manager+0xd0,node))return false;u32 budget=100000;
    while(node){u32 actor,next;if(!budget--||!m.read(node,actor)||!m.read(node+4,next))return false;
        if(actor&&!cleanup_enemy_actor(actor,manager,host,true))return false;node=next;
    }
    if(!m.write(manager+0x5c,0))return false;
    for(u32 at:{8,12}){u32 callback,flags;if(!m.read(manager+at,callback))return false;if(callback&&(!m.read(callback+4,flags)||!m.write(callback+4,flags&~2u)))return false;}
    return true;
}
bool cleanup_effect_resources(u32 owner,const std::array<u32,2>& heads,EnemyCleanupMemory& host){
    Memory m{host};for(u32 at:{0x10,0x14}){u32 resource;if(!m.read(owner+at,resource)||!m.mark_resources(resource,heads))return false;}return true;
}
}
