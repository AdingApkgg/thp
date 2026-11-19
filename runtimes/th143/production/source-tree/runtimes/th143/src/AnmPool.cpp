#include "AnmPool.hpp"
#include <algorithm>

namespace th143 {
AnmView AnmPool::at(u32 token){return token>=self&&std::uint64_t(token)+4<=std::uint64_t(self)+data.size()?AnmView{data.data()+token-self}:AnmView{nullptr};}
bool AnmPool::owns(u32 token)const{return token>=self+first&&token<self+free_node&&(token-self-first)%stride==0;}
bool AnmPool::construct(AnmPoolGlobals& globals,AnmPoolHost& host){
    std::fill(data.begin(),data.end(),0);auto s=view();
    // These global words are assignments, not a reset of unrelated transforms.
    for(u32 address:{0x5409e4,0x5409cc,0x5409b4,0x54099c,0x5409b8,0x5409d4,0x5409e8,0x5409ec,0x540a50,0x540a34,0x540a18,0x5409fc,0x540a20,0x540a40,0x540a58,0x540a5c})AnmView{globals.transforms.data()}.put(address-AnmPoolGlobals::base,word(1.f));
    for(u32 address:{0x5409a0,0x5409a4,0x5409bc,0x5409d0,0x540a04,0x540a08,0x540a24,0x540a3c})AnmView{globals.transforms.data()}.put(address-AnmPoolGlobals::base,0);
    s.put(0xbc8194,1);data[0xbc81a0]=255;
    for(u32 offset:{0x20,0x48,0x70,0x98})s.put(offset,0xffffffff);
    const u32 head=self+free_node;s.put(free_node,head);
    for(u32 i=0;i<count;++i){
        const u32 token=self+first+i*stride;auto vm=at(token);anm_reset(vm,token);vm.put(0x544,i);vm.data[0x5dc]=0;vm.put(0x5e0,i);
        const u32 node=token+0x5cc;vm.put(0x5cc,token);const u32 next=s.get(free_node+4);
        if(next){vm.put(0x5d0,next);at(next).put(8,node);}
        if(s.get(free_node+12))s.put(free_node+12,node);
        s.put(free_node+4,node);vm.put(0x5d4,head);
    }
    struct Callback {u32 entry;i32 priority;};
    for(auto c:{Callback{0x4839b0,34},{0x4839e0,9}})if(!host.register_pool_callback(c.entry,c.priority,false,self))return false;
    for(auto c:{Callback{0x4831a0,5},{0x4831b0,7},{0x4831c0,9},{0x4831d0,11},{0x4831e0,10},{0x483270,13},{0x483280,16},{0x483290,18},{0x4832a0,19},{0x4832b0,20},{0x4832c0,21},{0x4832d0,23},{0x483340,26},{0x4832e0,27},{0x4832f0,30},{0x483300,31},{0x483310,33},{0x483320,35},{0x483330,38},{0x483350,40},{0x483430,43},{0x483360,44},{0x483370,50},{0x483380,52},{0x4833c0,59},{0x4833b0,74},{0x483390,76},{0x4833a0,79},{0x4833d0,57},{0x4834d0,55},{0x483580,61},{0x483610,56},{0x4833e0,58},{0x4833f0,60},{0x4836b0,62},{0x483400,75},{0x483410,77},{0x483420,80}})if(!host.register_pool_callback(c.entry,c.priority,true,self))return false;
    return host.set_pool_vertex_format(0);
}
bool AnmPool::allocate(u32& token,AnmView& vm,AnmPoolHost& host){
    auto s=view();const u32 node=s.get(free_node+4);
    if(node){
        auto n=at(node);if(!n.data)return false;token=n.get(0);if(!owns(token))return false;vm=at(token);
        const u32 next=vm.get(0x5d0),previous=vm.get(0x5d4);
        if(next){auto p=at(next);if(!p.data)return false;p.put(8,previous);}
        if(previous){auto p=at(previous);if(!p.data)return false;p.put(4,next);}
        vm.put(0x5d0,0);vm.put(0x5d4,0);vm.put(0x544,vm.get(0x5e0));vm.data[0x5dc]=1;return true;
    }
    if(!host.allocate_pool_fallback(token,vm)||!vm.data)return false;
    anm_construct(vm);anm_reset(vm,token);vm.put(0x544,8191);return true;
}
bool AnmPool::return_slot(u32 token,AnmView vm){
    if(!owns(token)||vm.get(0x544)>=count)return false;
    const u32 index=vm.get(0x544);at(self+first+index*stride).data[0x5dc]=0;
    const u32 node=self+first+index*stride+0x5cc,head=self+free_node;auto s=view();auto n=at(node);const u32 next=s.get(free_node+4);
    if(next){n.put(4,next);at(next).put(8,node);}
    if(s.get(free_node+12))s.put(free_node+12,node);
    s.put(free_node+4,node);n.put(8,head);return true;
}
AnmView AnmPool::find(u32 handle){
    const u32 index=handle&8191;if(!handle||index>=count)return {nullptr};auto vm=at(self+first+index*stride);
    return vm.data[0x5dc]&&vm.get(0x540)==handle?vm:AnmView{nullptr};
}
}
