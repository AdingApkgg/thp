#include "AnmEffect7.hpp"
#include "DirectionVector.hpp"
#include "AnmRsqrtTable.hpp"
#include <cmath>

namespace th143 {
namespace {
using Vec=std::array<float,3>;
Vec load(AnmView s,u32 at){return {s.floating(at),s.floating(at+4),s.floating(at+8)};}
void store(AnmView s,u32 at,const Vec& v){for(u32 i=0;i<3;++i)s.put(at+i*4,word(v[i]));}
Vec add(Vec a,const Vec& b){for(u32 i=0;i<3;++i)a[i]+=b[i];return a;}
Vec sub(Vec a,const Vec& b){for(u32 i=0;i<3;++i)a[i]-=b[i];return a;}
Vec scale(Vec a,float f){for(float& v:a)v*=f;return a;}
bool normalize(Vec input,Vec& output){
    float length=input[0]*input[0];length+=input[1]*input[1];length+=input[2]*input[2];
    if(!std::isfinite(length))return false;
    if(length<real(0x28800000)){output={0,0,0};return true;}
    // Match the reference CPU's RSQRTSS estimate, then execute the DLL's
    // float refinement. Exact reciprocal sqrt is a different numeric path.
    const u32 bits=word(length);const i32 power=i32(bits>>23)-127;
    const u32 index=((bits&0x7fffff)|((u32(power)&1)<<23))>>12;
    const i32 exponent=power<0?(power-1)/2:power/2;
    const float estimate=real((0x3f000000u+(u32(anm_rsqrt_estimates[index])<<11))-(u32(exponent)<<23));
    float refine=estimate*length;refine*=estimate;
    const float half=estimate*.5f;refine=3.f-refine;refine*=half;
    output=scale(input,refine);return true;
}
bool polar(float angle,float magnitude,Vec& out){
    DirectionVector value;if(!direction_vector(angle,magnitude,value))return false;
    out={value.x,value.y,0};return true;
}
bool random_polar(Rng& rng,float radius,Vec& out){
    const float angle=rng.signed_unit()*real(0x40490fdb);
    const float magnitude=rng.unit()*radius;return polar(angle,magnitude,out);
}
void curve(AnmView s,u32 duration,const Vec& start,const Vec& from,const Vec& target,const Vec& to,u32 rate){
    s.put(0xec,duration);s.put(0xf0,8);store(s,0x9c,start);store(s,0xa8,target);store(s,0xb4,from);store(s,0xc0,to);
    if(!(s.get(0xe8)&1)){s.put(0xe4,rate);s.put(0xe8,s.get(0xe8)|1);}
    s.put(0xd8,0xffffffff);s.put(0xdc,0);s.put(0xe0,0);
}
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
bool timer(AnmView t,AnmEffect7Host& host,float increment,bool always_fraction){
    float rate=1.f;const u32 token=t.get(12),current=t.get(4);
    if(token&&!host.timer_rate(token,rate))return false;
    const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));t.put(0,current);
    if(always_fraction){const float f=t.floating(8)+(unit?increment:rate*increment);t.put(8,word(f));t.put(4,truncate(f));}
    else if(unit){t.put(4,current+1);t.put(8,word(t.floating(8)+1.f));}
    else{const float f=t.floating(8)+rate;t.put(8,word(f));t.put(4,truncate(f));}
    return true;
}
}
i32 anm_effect7_step(AnmView root,u8* data,AnmEffect7Host& host){
    AnmView extra{data};const Vec position=load(root,0x59c);Vec direction;
    if(!polar(root.floating(0x50),300.f,direction))return -2;
    const Vec far=add(direction,position);store(extra,0x190c,far);store(extra,0x1918,position);
    if(!polar(root.floating(0x4d4)+root.floating(0x50),150.f,direction))return -2;
    const Vec near=add(position,direction);store(extra,0x1900,near);
    const i32 current=signed_word(extra.get(0x192c));
    if(extra.get(0x192c)!=extra.get(0x1928)&&current<50){
        if(current<0)return -2;
        const u32 first=u32(current)*4;
        for(u32 i=0;i<4;++i){u32 handle;if(!host.create(i==3?144:143,handle))return -2;extra.put((first+i)*4,handle);}
        u32 inverted=root.get(0x534);
        for(u32 i=0;i<3;++i){const u32 shift=i*8;inverted=(inverted&~(255u<<shift))|(u32(u8(44-u8(inverted>>shift)))<<shift);}
        for(u32 i=0;i<4;++i){auto vm=host.find(extra.get((first+i)*4));if(!vm.data)return -2;vm.put(0x534,i==3?inverted:root.get(0x534));vm.put(0x4ac,root.get(0x4ac));}
    }
    u32 live=0;float slowdown;if(!host.slowdown(root,slowdown))return -2;
    for(u32 i=0;i<200;++i){
        auto vm=host.find(extra.get(i*4));if(!vm.data){extra.put(i*4,0);continue;}vm.put(0x598,word(slowdown));
        const u32 state=extra.get(0x15e0+i*4),duration=root.get(0x4ac);
        if(!state){
            Vec offset;if(!random_polar(host.rng(),150.f,offset))return -2;
            const Vec start=add(far,offset);
            if(!random_polar(host.rng(),50.f,offset))return -2;
            const Vec target=add(near,offset);Vec forward,backward,finish;
            if(!normalize(sub(target,start),forward)||!normalize(sub(position,target),backward))return -2;
            const float end_scale=host.rng().unit()*200.f+200.f;
            if(!normalize(add(forward,backward),finish))return -2;finish=scale(finish,end_scale);
            const float start_scale=host.rng().unit()*100.f+100.f;
            Vec initial;if(!normalize(sub(target,start),initial))return -2;initial=scale(initial,start_scale);
            curve(vm,duration,start,initial,target,finish,host.global_rate_token());store(extra,0x320+i*12,target);store(extra,0xc80+i*12,finish);extra.put(0x15e0+i*4,1);
        }else if(state==1&&signed_word(vm.get(0x560))>=signed_word(duration+1)){
            Vec offset,finish;if(!random_polar(host.rng(),20.f,offset)||!random_polar(host.rng(),20.f,finish))return -2;
            curve(vm,duration,load(extra,0x320+i*12),load(extra,0xc80+i*12),add(position,offset),finish,host.global_rate_token());extra.put(0x15e0+i*4,2);
        }
        ++live;
    }
    if(!live)return -1;
    return timer(extra.sub(0x1928),host,1.f,false)?0:-2;
}
bool anm_effect7_cancel(u8* data,AnmEffect7Host& host){
    AnmView extra{data};for(u32 i=0;i<200;++i){auto vm=host.find(extra.get(i*4));if(!vm.data)extra.put(i*4,0);else{vm.put(0x18,vm.get(0x18)&~1u);vm.put(0x28,0);}}return true;
}
bool anm_effect7_signal(u8* data,i32 signal,AnmEffect7Host& host){return signal!=1||timer(AnmView{data}.sub(0x1928),host,300.f,true);}
}
