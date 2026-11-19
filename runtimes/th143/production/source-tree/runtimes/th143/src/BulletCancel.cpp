#include "BulletCancel.hpp"
namespace th143 {
bool bullet_cancel_item(const std::array<float,3>& p,i32 kind,BulletCancelGlobals& g,BulletCancelHost& host){
    if(!kind||-192.f>=p[0]+32.f||p[0]-32.f>=192.f||0.f>=p[1]+32.f||p[1]-32.f>=448.f)return true;
    ++g.cancelled;
    if(kind==1){
        const float angle=g.gameplay_rng.signed_unit()*real(0x3e32b8c2)-real(0x3fc90fdb);
        ++g.item_counter;return host.cancel_item(14,p,angle,real(0x3fe66666));
    }
    if(kind==3){g.gameplay_rng.signed_unit();++g.item_counter;}
    else if(kind==2){
        if(signed_word(g.cancelled)%5==0){if(g.special_flags&1)return true;++g.item_counter;}
        if(g.special_flags&1)return true;
    }else return true;
    g.gameplay_rng.signed_unit();++g.item_counter;return true;
}
bool cancel_bullet(BulletView b,i32 kind,u32 resource,const float& elapsed,BulletCancelGlobals& g,AnmWorld& world,BulletCancelHost& host){
    if(!signal_animation_vm(world,{b.data+0x28},1,false,&host))return false;
    if((b.get(0x60c)&1)&&!signal_animation_vm(world,{b.data+0x5f4},1,false,&host))return false;
    if(!(b.get(0x20)&0x200)){
        const std::array<float,3> position{b.floating(0xbc0),b.floating(0xbc4),b.floating(0xbc8)};
        const i32 script=signed_word(b.get(0xc00));
        if(script>=0){u32 ignored;if(!world.create_at(resource,script,-1,position,ignored))return false;}
        if(!host.cancel_sound(71,b.floating(0xbc0)))return false;
        const std::array<float,3> live{b.floating(0xbc0),b.floating(0xbc4),b.floating(0xbc8)};
        if(!bullet_cancel_item(live,kind,g,host))return false;
    }
    const float rate=elapsed;
    for(u32 i=0;i<3;++i){const float delta=(b.floating(0xbcc+i*4)*rate)*.5f;b.put(0xbc0+i*4,word(b.floating(0xbc0+i*4)+delta));}
    b.state(4);const u32 flags=b.get(0x13d0);
    if(!(flags&1)){b.put(0x13cc,world.global_rate_token());b.put(0x13d0,flags|1);}
    b.put(0x13c0,0xffffffff);b.put(0x13c4,0);b.put(0x13c8,0);return true;
}
bool cancel_bullets_circle(u32 manager,const std::array<float,3>& p,float radius,i32 kind,bool include_delayed,const float& elapsed,BulletCancelGlobals& g,AnmWorld& world,BulletCancelHost& host){
    auto read=[&](u32 at,u32& value){return host.cancel_read(at,&value,4);};
    auto write=[&](u32 at,u32 value){return host.cancel_write(at,&value,4);};
    u32 node,next=0,bullet=0;if(!read(manager+0x80,node)||!write(manager+0x9bf6c0,node))return false;
    if(node&&!read(node+4,next))return false;
    if(!write(manager+0x9bf6c4,next)||node&&!read(node,bullet))return false;
    u32 budget=100000;
    while(bullet){
        if(!budget--)return false;BulletView b{nullptr};if(!host.cancel_bullet_view(bullet,b)||!b.data)return false;
        if((b.state()==1||b.state()==2)&&(include_delayed||!b.get(0x24))){
            const float reach=b.floating(0xbe0)*.5f+radius;
            const float dx=b.floating(0xbc0)-p[0],dy=b.floating(0xbc4)-p[1];
            if(reach*reach>=dx*dx+dy*dy){u32 resource;if(!read(manager+0x9bf6cc,resource)||!cancel_bullet(b,kind,resource,elapsed,g,world,host))return false;}
        }
        if(!read(manager+0x9bf6c4,node)||!write(manager+0x9bf6c0,node))return false;
        next=0;if(node&&!read(node+4,next))return false;
        if(!write(manager+0x9bf6c4,next))return false;
        bullet=0;if(node&&!read(node,bullet))return false;
    }
    return host.cancel_enemy_circle(p,radius,kind);
}
}
