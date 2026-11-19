#include "PlayerInit.hpp"
#include <cmath>

namespace th143 {
bool PlayerShotData::load(const u8* raw,u32 n,u32 base,u32 collision){
    if(n<0x108||std::uint64_t(base)+n>0x100000000ull)return false;
    data.assign(raw,raw+n);token=base;
    const u32 count=u32(data[2])|(u32(data[3])<<8);
    if(count>10)return false;
    static constexpr u32 spawn[]={0,0x4519e0,0x451c20,0x452610,0x452e10,0x452f20,0x453130};
    static constexpr u32 motion[]={0,0x451a00,0x451e00,0x452660,0x453000,0x452ea0,0x452fa0,0x4531f0,0x453970};
    static constexpr u32 cancel[]={0,0x452180,0x452400,0x452970,0x453020,0x453930,0x4535e0,0x453990,0x452fe0};
    for(u32 i=0;i<count;++i){
        const u32 offset=get(0xe0+i*4);if(std::uint64_t(offset)+0x108>=n)return false;
        u32 at=offset+0x108;put(0xe0+i*4,base+at);
        while(at<n&&i32(std::int8_t(data[at]))>=0){
            if(std::uint64_t(at)+0x58>n)return false;
            const u32 a=get(at+0x28),b=get(at+0x2c),c=get(at+0x30),d=get(at+0x34);
            if(a>=7||b>=9||c!=0||d>=9)return false;
            put(at+0x28,spawn[a]);put(at+0x2c,motion[b]);put(at+0x30,collision);put(at+0x34,cancel[d]);at+=0x58;
        }
        if(at>=n)return false;
    }
    return true;
}
void player_construct(PlayerState& p){p.data.fill(0);}
namespace {
void timer(PlayerState& p,u32 at,i32 value,u32 rate){
    if(!(p.get(at+16)&1)){p.put(at+12,rate);p.put(at+16,p.get(at+16)|1);}
    p.put(at,u32(value-1));p.put(at+4,u32(value));p.put(at+8,word(float(value)));
}
i32 truncate(float v){if(!std::isfinite(v)||v>=2147483648.f||v< -2147483648.f)return i32(0x80000000u);return i32(v);}
}
bool player_initialize(PlayerState& p,PlayerShotData& sht,const PlayerInitConfig& c,PlayerPower& power,PlayerInitHost& host){
    if(sht.data.size()<0x108||!sht.token)return false;
    p.put(0x10,c.resource);p.put(0x688,sht.token);p.put(8,c.update_callback);p.put(12,c.draw_callback);
    if(!host.bind_initial_visual(p))return false;
    p.put(0x5e0,0);p.put(0x5e4,word(400.f));p.put(0x5ec,0);p.put(0x5f0,51200);
    for(u32 i=0;i<4;++i)p.put(0x5f4+i*4,u32(truncate(sht.floating(0x10+i*4)*128.f)));
    sht.put(0x24,100);power.maximum=sht.get(0x20)*sht.get(0x24);power.step=sht.get(0x24);
    timer(p,0x182ec,-1,c.rate);sht.put(4,word(3.f));sht.put(12,word(60.f));sht.put(8,word(5.f));
    p.put(0x648,word(sht.floating(4)*.5f));p.put(0x64c,p.get(0x648));p.put(0x650,word(5.f));
    p.put(0x654,word(30.f));p.put(0x658,word(30.f));p.put(0x65c,word(5.f));
    p.put(0x660,word(50.f));p.put(0x664,word(50.f));p.put(0x668,word(5.f));
    for(auto pair:{std::array<u32,2>{0x630,0x648},{0x18310,0x654},{0x18328,0x660},{0x18340,0x660}}){
        for(u32 i=0;i<3;++i){const float position=p.floating(0x5e0+i*4),half=p.floating(pair[1]+i*4);
            p.put(pair[0]+i*4,word(position-half));p.put(pair[0]+12+i*4,word(position+half));}
    }
    timer(p,0x68c,0,c.rate);timer(p,0x6b4,0,c.rate);timer(p,0x18468,0,c.rate);
    p.put(0x182bc,30);p.put(0x182e8,0);p.put(0xd6dc,word(1.f));
    const u32 head=0xd6c8;p.put(head,c.self+head);p.put(head+4,0);p.put(head+8,0);p.put(head+12,0);
    for(u32 i=0;i<256;++i){const u32 at=0x6c8+i*0xd0,old=p.get(head+4);
        p.put(at,c.self+at);p.put(at+4,old);p.put(at+8,c.self+head);p.put(at+12,0);
        if(old)p.put(old-c.self+8,c.self+at);
        p.put(head+4,c.self+at);
    }
    for(u32 i=0;i<33;++i){p.put(0x1845c-i*8,p.get(0x5ec));p.put(0x18460-i*8,p.get(0x5f0));}
    for(u32 i=0;i<8;++i)p.put(0xd74c+i*0xe4,0xffff3800);
    p.put(0x184a8,0);p.put(0x184b0,word(1.f));
    const u32 flags=p.get(0x1847c)&0xfffffe4d;p.put(0x1847c,((flags&0x200)<<1)|(flags&0xfffff9ff));
    return true;
}
}
