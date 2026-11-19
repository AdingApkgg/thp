#include "AnmSignal.hpp"
namespace th143 {
namespace {
bool apply(AnmWorld& world,AnmView vm,i32 signal,AnmSignalHost* host){
    const u32 entry=vm.get(0x5c4);
    if(entry==0x408230){
        bool found=false;for(auto& extra:world.extras)if(extra->token==vm.get(0x5b4)){
            if(!anm_effect7_signal(extra->data.data(),signal,world))return false;found=true;break;
        }if(!found)return false;
    }else if(entry&&(!host||!host->animation_signal_callback(entry,vm,signal))){world.error=entry;return false;}
    vm.put(0x4a0,u32(signal));return true;
}
}
bool signal_animation_vm(AnmWorld& world,AnmView vm,i32 signal,bool immediate,AnmSignalHost* host){
    if(!vm.data)return false;
    if(!apply(world,vm,signal,host))return false;
    if(immediate&&anm_step(vm,world)==-2){u16 opcode=0;world.read(vm.get(0x28),&opcode,2);world.error=opcode;return false;}
    return true;
}
bool signal_animation(AnmWorld& world,u32 handle,i32 signal,bool immediate,AnmSignalHost* host){
    auto vm=world.find(handle);if(!vm.data)return true;
    if(!signal_animation_vm(world,vm,signal,immediate,host))return false;
    if(vm.get(0x588))return true;
    u32 node=vm.get(0x584),budget=0;
    while(node){
        u32 token,next;if(++budget>100000||!world.read(node,&token,4))return false;
        auto child=world.state(token);if(!child.data||!apply(world,child,signal,host))return false;
        if(immediate){if(!world.read(node,&token,4))return false;auto target=world.state(token);if(!target.data||anm_step(target,world)==-2)return false;}
        if(!world.read(node+4,&next,4))return false;node=next;
    }return true;
}
}
