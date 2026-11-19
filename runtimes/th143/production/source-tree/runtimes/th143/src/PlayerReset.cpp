#include "PlayerReset.hpp"
namespace th143 {
namespace {
void timer(PlayerState& p,u32 at,i32 value,u32 rate){
    if(!(p.get(at+16)&1)){p.put(at+12,rate);p.put(at+16,p.get(at+16)|1);}
    p.put(at,u32(value)-1);p.put(at+4,u32(value));p.put(at+8,word(float(value)));
}
bool signal(u32 handle,AnmWorld& graphics,PlayerResetHost& host){
    auto vm=graphics.find(handle);if(!vm.data)return true;
    auto apply=[&](AnmView v){if(v.get(0x5c4)&&!host.reset_visual_callback(v.get(0x5c4),v,2))return false;v.put(0x4a0,2);return true;};
    if(!apply(vm))return false;if(vm.get(0x588))return true;
    u32 node=vm.get(0x584),budget=0;
    while(node){auto at=graphics.instances.registry.nodes.find(node-0x580);if(at==graphics.instances.registry.nodes.end()||++budget>graphics.states.size())return false;auto child=at->second;if(!apply(child))return false;node=child.get(0x584);}return true;
}
}
bool reset_player(PlayerState& p,u32 self,i32 lives,u32 fragments,AnmWorld& graphics,PlayerResetHost& host){
    p.put(0x684,1);const u32 rate=graphics.global_rate_token();timer(p,0x182ec,-1,rate);
    for(u32 at:{0x68c,0x6a0,0x6b4})timer(p,at,0,rate);
    for(u32 i=0;i<33;++i){p.put(0x1845c-i*8,p.get(0x5ec));p.put(0x18460-i*8,p.get(0x5f0));}
    const u32 head=0xd6c8;p.put(head,self+head);p.put(head+4,0);p.put(head+8,0);p.put(head+12,0);
    for(u32 i=0;i<256;++i){const u32 at=0x6c8+i*0xd0,previous=p.get(head+4);p.put(at,self+at);p.put(at+4,0);p.put(at+8,0);p.put(at+12,0);
        if(previous){p.put(at+4,previous);p.put(previous-self+8,self+at);}p.put(head+4,self+at);p.put(at+8,self+head);}
    p.put(0x1847c,p.get(0x1847c)&~0x24u);
    if(!graphics.mark_retirement(p.get(0xd6d8)))return false;p.put(0xd6d8,0);p.put(0xd6d8,0);
    if(!host.reset_lives(lives,fragments))return false;p.put(0x1847c,p.get(0x1847c)&~1u);
    for(u32 i=0;i<8;++i)for(u32 at:{0xd79cu,0xd7a0u})if(!signal(p.get(at+i*0xe4),graphics,host))return false;
    p.put(0x1847c,p.get(0x1847c)&~0x12u);p.put(0x182c0,0);p.put(0xd6dc,word(1.f));
    for(u32 at=0x18300;at<=0x1830c;at+=4)p.put(at,0);timer(p,0x182c4,0,rate);
    for(u32 at:{0x184c0,0x184c4,0x184c8,0xde14,0x184a8})p.put(at,0);p.put(0x184b0,word(1.f));return true;
}
}
