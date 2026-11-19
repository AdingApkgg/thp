#include "AnmEffect5.hpp"

namespace th143 {
void anm_effect5_initialize(AnmView s,u8* data,u32 token,u32 rate,Rng& random){
    std::memset(data,0,0x418);AnmView e{data};
    e.put(0x400,word(random.signed_unit()*real(0x40490fdb)));
    e.put(0x404,0);e.put(0x408,1);e.put(0x40c,word(1.f));e.put(0x410,rate);e.put(0x414,1);
    for(u32 i=0;i<16;++i){e.put(0x300+i*12,word(3.f));e.put(0x304+i*12,0);e.put(0x308+i*12,word(-16.f));}
    for(u32 i=0;i<3;++i)s.put(0x59c+i*4,s.get(i*4));s.put(0x24,15);s.put(0x5b4,token);
    s.put(0x5b8,0x409ec0);s.put(0x5bc,0x40a120);s.put(0x5c0,0x40a1a0);s.put(0x5c4,0x40a1b0);
}
bool anm_effect5_step(u8* data,AnmTimerHost& host,Rng& random){
    AnmView e{data};const u32 current=e.get(0x408);
    if((current&3)==0){
        for(u32 i=15;i;--i)std::memcpy(data+0x300+i*12,data+0x300+(i-1)*12,12);
        float x=e.floating(0x300);
        if(x>=3.f)x-=random.unit()*.1f;
        else x+=(x<=0.f?random.unit():random.signed_unit())*.1f;
        e.put(0x300,word(x));
    }
    float x=0,y=0,z=0,width=0;
    for(u32 i=0;i<16;++i){const u32 p=i*48;const float v=float(i)*.0625f;
        for(auto item:{std::pair<u32,u32>{p,word(x+width)},{p+4,word(y)},{p+8,word(z)},{p+12,0x80ffffff},{p+16,0},{p+20,word(v)},{p+24,word(x-width)},{p+28,word(y)},{p+32,word(z)},{p+36,0x80ffffff},{p+40,word(1.f)},{p+44,word(v)}})e.put(item.first,item.second);
        if(width<8.f)width+=2.f;x+=e.floating(0x300+i*12);y+=e.floating(0x304+i*12);z+=e.floating(0x308+i*12);
    }
    for(u32 at:{0x2dc,0x2f4,0xc,0x24,0x174,0xfc,0x24c,0x54,0x12c,0x294})e.put(at,0x00ffffff);
    e.put(0x2ac,0x50ffffff);e.put(0x2c4,0x50ffffff);e.put(0x27c,0xb0ffffff);
    float rate=1;const u32 pointer=e.get(0x410);if(pointer&&!host.timer_rate(pointer,rate))return false;
    const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float elapsed=e.floating(0x40c)+(unit?1.f:rate);
    e.put(0x404,current);e.put(0x40c,word(elapsed));e.put(0x408,unit?current+1:elapsed>=-2147483648.f&&elapsed<2147483648.f?u32(i32(elapsed)):0x80000000);return true;
}
}
