#include "AnmManager.hpp"
using namespace th11;
namespace {u32 words[4];void increment(AnmVm& vm){vm.extra_integers[0]=signed_bits(u32(vm.extra_integers[0])+1);}}
extern "C" __attribute__((export_name("ordering_case"))) u32 ordering_case(u32 initial,u32 overlay){
    AnmResource resource;resource.scripts.resize(1);
    const AnmInstruction stop{2,8,0,0};resource.scripts[0].bytes.resize(sizeof stop);std::memcpy(resource.scripts[0].bytes.data(),&stop,sizeof stop);
    AnmManager manager;if(!manager.prepare_resource(resource,1))return 0;
    auto* vm=manager.create(resource,0,1,overlay?34:0,overlay!=0);if(!vm)return 0;
    vm->before_update=increment;vm->extra_integers[0]=signed_bits(initial);
    vm->instruction=reinterpret_cast<AnmInstruction*>(resource.scripts[0].bytes.data());vm->flags|=0x20000;
    words[0]=words[1]=0;words[2]=words[3]=0;
    const auto boundary=[&](const AnmVm& current,AnmManager::VmBoundaryTh14 point){
        if(current.id!=vm->id)return false;
        const u32 at=u32(point);words[at]=u32(current.extra_integers[0]);++words[2+at];return true;
    };
    return manager.update(overlay!=0,AnmManager::VmBoundaryCallbackTh14(boundary));
}
extern "C" __attribute__((export_name("ordering_word"))) u32 ordering_word(u32 index){return index<4?words[index]:~0u;}
