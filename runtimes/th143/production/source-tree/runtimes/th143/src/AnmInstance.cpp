#include "AnmInstance.hpp"

namespace th143 {
namespace {
void zero_timer(AnmView t,u32 rate) {
    if(!(t.get(16)&1)){t.put(12,rate);t.put(16,t.get(16)|1);}
    t.put(0,0xffffffff);t.put(4,0);t.put(8,0);
}
}
void anm_copy_template(AnmView target,u32 self,AnmView source,u32 rate) {
    const u32 layer=target.get(0x24),index=target.get(0x544);
    const std::array<u32,3> position{target.get(0x59c),target.get(0x5a0),target.get(0x5a4)};
    std::memset(target.data+0x540,0,0x8c);
    target.put(0x24,layer);target.put(0x544,index);
    for(u32 i=0;i<3;++i)target.put(0x59c+i*4,position[i]);
    target.put(0x570,self);target.put(0x580,self);
    std::memcpy(target.data,source.data,0x540);
    zero_timer(target.sub(0x55c),rate);zero_timer(target.sub(0x548),rate);
}
bool anm_create_instance(AnmView target,u32 self,AnmView source,i32 layer,AnmVmHost& host) {
    anm_copy_template(target,self,source,host.global_rate_token());
    target.put(0x1c,target.get(0x1c)|0x200);
    if(layer>=0){
        target.put(0x24,u32(layer));
        if(layer<=23)target.put(0x1c,(target.get(0x1c)&~0x40000u)|0x20000);
    }
    for(u32 i=0;i<3;++i)target.put(0x59c+i*4,0);
    target.put(0x50,0);
    return anm_step(target,host)!=-2;
}
void AnmRegistry::sync_owner(){if(owner.data){owner.put(0xfe8218,primary_head);owner.put(0xfe821c,primary_tail);owner.put(0xfe8220,secondary_head);owner.put(0xfe8224,secondary_tail);owner.put(0xff75a0,generation);}}
bool AnmRegistry::insert(AnmView s,u32 self,bool secondary,bool prepend,u32& handle) {
    const u32 index=s.get(0x544)&8191;
    if((index!=8191&&(index>=pool.size()||pool[index].data!=s.data||!s.data[0x5dc]))||nodes.count(self))return false;
    u32& head=secondary?secondary_head:primary_head;
    u32& tail=secondary?secondary_tail:primary_tail;
    s.put(0x570,self);s.put(0x574,0);s.put(0x578,0);s.put(0x57c,0);
    if(!head)head=tail=self+0x570;
    else if(prepend){
        auto at=nodes.find(head-0x570);if(at==nodes.end())return false;
        s.put(0x574,head);at->second.put(0x578,self+0x570);head=self+0x570;
    }else{
        auto at=nodes.find(tail-0x570);if(at==nodes.end())return false;
        at->second.put(0x574,self+0x570);s.put(0x578,tail);tail=self+0x570;
    }
    generation=(generation+1)&0x7ffff;if(!generation)++generation;
    handle=(generation<<13)|(s.get(0x544)&8191);s.put(0x540,handle);
    nodes.emplace(self,s);sync_owner();return true;
}
AnmView AnmRegistry::find(u32 id) const {
    if(!id)return {nullptr};
    const u32 index=id&8191;if(index!=8191){if(index>=pool.size())return {nullptr};auto vm=pool[index];return vm.data[0x5dc]&&vm.get(0x540)==id?vm:AnmView{nullptr};}
    for(u32 head:{primary_head,secondary_head}){
        while(head){
            const auto at=nodes.find(head-0x570);if(at==nodes.end())return {nullptr};
            if(at->second.get(0x540)==id)return at->second;
            head=at->second.get(0x574);
        }
    }
    return {nullptr};
}
bool AnmInstances::create(u32 resource,AnmView target,u32 self,AnmView source,i32 layer,AnmVmHost& host,u32& handle,bool secondary,bool prepend) {
    ++resource_uses[resource];
    return anm_create_instance(target,self,source,layer,host)&&registry.insert(target,self,secondary,prepend,handle);
}
bool AnmInstances::child(u32 resource,AnmView target,u32 self,AnmView source,AnmView parent,u32 parent_token,u32 flags,AnmVmHost& host,u32& handle) {
    ++resource_uses[resource];
    target.put(0x1c,target.get(0x1c)|0x200);target.put(0x24,parent.get(0x24));
    for(u32 i=0;i<3;++i)target.put(0x59c+i*4,0);
    // These prefix writes happen BEFORE40ab20 in the original and are
    // overwritten by the template; do not "correct" them after copying.
    anm_copy_template(target,self,source,host.global_rate_token());
    target.put(0x594,parent_token);
    target.put(0x1c,(target.get(0x1c)&~0x1000000u)|(parent.get(0x1c)&0x1000000));
    if(anm_step(target,host)==-2||!registry.insert(target,self,(flags&4)!=0,(flags&2)!=0,handle))return false;
    const u32 next=parent.get(0x584);
    if(next){
        auto at=registry.nodes.find(next-0x580);if(at==registry.nodes.end())return false;
        target.put(0x584,next);at->second.put(0x588,self+0x580);
    }
    if(parent.get(0x58c))parent.put(0x58c,self+0x580);
    parent.put(0x584,self+0x580);target.put(0x588,parent_token+0x580);
    return true;
}
void anm_effect7_initialize(AnmView s,u8* data,u32 token,u32 rate) {
    std::memset(data,0,0x193c);AnmView extra{data};
    extra.put(0x1928,0xffffffff);extra.put(0x1934,rate);extra.put(0x1938,1);
    s.put(0x5b4,token);s.put(0x5b8,0x407670);s.put(0x5bc,0x4081e0);s.put(0x5c0,0x4081f0);s.put(0x5c4,0x408230);
}
}
