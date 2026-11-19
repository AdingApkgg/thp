#include "PlayerMovement.hpp"
#include <cmath>
#include <algorithm>

namespace th143 {
namespace {
i32 integer(u32 v){return signed_word(v);}
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000u;}
void place(AnmView vm,const std::array<float,3>& p){if(vm.data)for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(p[i]));}
}
bool player_movement(PlayerState& p,const PlayerMovementInput& in,PlayerMovementHost& host){
    const u32 keys=in.keys;u32 direction;
    if((keys&0x50)==0x50)direction=5;
    else if((keys&0x60)==0x60)direction=7;
    else if((keys&0x90)==0x90)direction=6;
    else if((keys&0xa0)==0xa0)direction=8;
    else if(keys&0x20)direction=2;
    else if(keys&0x10)direction=1;
    else if(keys&0x40)direction=3;
    else if(keys&0x80)direction=4;
    else direction=0;
    p.put(0x680,direction);
    if(in.gameplay&&integer(p.get(0x6a4))>=4)p.put(0x18464,(keys>>3)&1);
    else{p.put(0x18464,0);p.put(0x182bc,30);}
    if(p.get(0x1847c)&0x10){direction=0;p.put(0x680,0);p.put(0x18464,0);}
    static constexpr i32 vectors[9][2]={{0,0},{0,-1},{0,1},{-1,0},{1,0},{-1,-1},{1,-1},{-1,1},{1,1}};
    u32 speed;
    if(p.get(0x18464)){
        if(!p.get(0xd6d8)){u32 handle=0;if(!host.create_focus(in.alternate_focus&&in.equipment==4?18:16,handle))return false;p.put(0xd6d8,handle);}
        auto vm=host.visual(p.get(0xd6d8));if(!vm.data)return false;
        const float scale=p.get(0x1847c)&8?(p.floating(0x184b0)-1.f)*2.f+1.f:1.f;
        vm.put(0x68,word(scale));vm.put(0x6c,word(scale));vm.put(0x18,vm.get(0x18)|8);
        speed=p.get(direction>=5?0x600:0x5f8);
    }else{
        if(!host.signal_visual(p.get(0xd6d8),1))return false;p.put(0xd6d8,0);
        speed=p.get(direction>=5?0x5fc:0x5f4);
    }
    u32 delta[2];
    for(u32 i=0;i<2;++i){const u32 raw=speed*u32(vectors[direction][i])-truncate(p.floating(0xd6e0+i*4)*-128.f);
        delta[i]=truncate(float(integer(raw))*p.floating(0xd6dc));}
    auto bind=[&](i32 script){return host.bind_player_visual(p,script);};
    if(!(p.get(0x1847c)&0x200)){
        if(p.get(0x1847c)&0x400){if(!bind(4))return false;p.put(0x1847c,p.get(0x1847c)&~0x400u);}
        const i32 dx=integer(delta[0]),old=integer(p.get(0x678));
        if(dx<0&&old>=0){if(!bind(1))return false;}
        if(dx>0&&old<=0){if(!bind(3))return false;}
        else if(dx==0&&old<0){if(!bind(2))return false;}
        if(dx==0&&old>0){if(!bind(4))return false;}
    }else if(!(p.get(0x1847c)&0x400)){if(!bind(5))return false;p.put(0x1847c,p.get(0x1847c)|0x400);}
    for(u32 i=0;i<2;++i){p.put(0x678+i*4,delta[i]);p.put(0x604+i*4,word(float(integer(delta[i]))*in.elapsed));}
    if(direction)for(u32 i=0;i<3;++i)p.put(0x610+i*4,p.get(0x604+i*4));
    for(u32 i=0;i<2;++i){const u32 v=truncate(p.floating(0x604+i*4));p.put(0x61c+i*4,v);p.put(0x5ec+i*4,p.get(0x5ec+i*4)+v);}
    if(!(p.get(0x1847c)&0x40)){
        p.put(0x5ec,u32(std::max(-23552,std::min(23552,integer(p.get(0x5ec))))));
        p.put(0x5f0,u32(std::max(4096,std::min(55296,integer(p.get(0x5f0))))));
    }
    p.put(0x1847c,p.get(0x1847c)&~0x40u);
    p.put(0x5e0,word(float(integer(p.get(0x5ec)))*.0078125f));p.put(0x5e4,word(float(integer(p.get(0x5f0)))*.0078125f));
    auto focus=host.visual(p.get(0xd6d8));if(!focus.data)p.put(0xd6d8,0);
    else place(focus,{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)});
    if(delta[0]||delta[1]){
        const i32 lag=integer(p.get(0x182e8));if(lag<0||lag>4)return false;
        u32 n=32;
        if(u32(lag)*8<n)while(n>u32(lag)*8){p.put(0x1835c+n*8,p.get(0x1835c+u32(lag)*64));p.put(0x18360+n*8,p.get(0x18360+u32(lag)*64));--n;}
        while(n){p.put(0x1835c+n*8,p.get(0x1835c+(n-1)*8));p.put(0x18360+n*8,p.get(0x18360+(n-1)*8));--n;}
    }
    p.put(0x1835c,p.get(0x5ec));p.put(0x18360,p.get(0x5f0));
    if(p.get(0x1847c)&1)p.put(0x182c0,p.get(0x182c0)+1);
    for(u32 i=0;i<8;++i){const u32 at=0xd6ec+i*0xe4;
        if(!p.get(at))continue;
        if(!(p.get(0x1847c)&1)){
            const u32 offset=at+(p.get(0x18464)?0x6c:0x64);
            p.put(at+0x54,p.get(0x5ec)+p.get(offset));p.put(at+0x58,p.get(0x5f0)+p.get(offset+4));
            if(p.get(at+0xdc)&&!host.option_callback(p,at,p.get(at+0xdc)))return false;
        }else{
            p.put(at+0x54,p.get(0x5ec));p.put(at+0x58,p.get(0x5f0));
            if(integer(p.get(0x182c0))>=30){
                p.put(at,0);if(!host.signal_visual(p.get(at+0xb0),1)||!host.signal_visual(p.get(at+0xb4),1))return false;
                p.put(0x182e8,0);continue;
            }
        }
        bool snap=p.get(at+0xd4)!=0;
        if(snap)p.put(at+0xd4,0);
        else if(integer(p.get(0x182bc))>=30){
            const u32 amount=p.get(0x182bc);
            const i32 dx=integer((p.get(at+0x54)-p.get(at+0x5c))*amount)/100;
            const i32 dy=integer((p.get(at+0x58)-p.get(at+0x60))*amount)/100;
            if(!dx&&!dy)snap=true;
            else{p.put(at+0x5c,p.get(at+0x5c)+u32(dx));p.put(at+0x60,p.get(at+0x60)+u32(dy));}
        }
        if(snap){p.put(at+0x5c,p.get(at+0x54));p.put(at+0x60,p.get(at+0x58));}
        const std::array<float,3> position{float(integer(p.get(at+0x5c)))*.0078125f,float(integer(p.get(at+0x60)))*.0078125f,0};
        place(host.visual(p.get(at+0xb0)),position);place(host.visual(p.get(at+0xb4)),position);
    }
    return true;
}
}
