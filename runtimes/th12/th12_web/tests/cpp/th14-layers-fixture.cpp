#include "../../cpp/game/AnmManager.hpp"
using namespace th11;
static AnmManager manager;static AnmResource resource;
static u32 identities[8],updates[8],update_count;
static int after(AnmVm& vm){updates[update_count++]=vm.integers[0];vm.layer=vm.integers[2];return vm.integers[1];}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) int run(u32 overlay,u32 start,u32 variant){
    manager.clear();resource={};resource.scripts.resize(1);const AnmInstruction idle{0,8,30000,0};resource.scripts[0].bytes.resize(8);std::memcpy(resource.scripts[0].bytes.data(),&idle,8);
    for(u32 i=0;i<8;++i){auto* vm=manager.create(resource,0,0,(start+i*7)%34,overlay);if(!vm)return -1;identities[i]=vm->id;
        vm->integers[0]=i;vm->integers[1]=variant==1&&i%3==0;vm->integers[2]=(start+i*7+variant)%(overlay?40:34);vm->after_update=after;
        if(variant==2&&i%3==1)vm->flags2|=0x20;
    }
    update_count=0;return manager.update(overlay);
}
API(updates_size) u32 updates_size(){return update_count;}
API(update_value) u32 update_value(u32 i){return updates[i];}
API(alive) u32 alive(u32 i){return manager.find(identities[i])!=nullptr;}
API(layer_value) int layer_value(u32 layer,u32 index){auto* vm=manager.layer_first(layer);for(u32 i=0;i<index&&vm;++i)vm=vm->draw_next;if(!vm)return -1;for(u32 i=0;i<8;++i)if(vm->id==identities[i])return i;return -2;}
