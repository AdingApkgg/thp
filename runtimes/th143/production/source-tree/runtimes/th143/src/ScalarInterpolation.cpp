#include "ScalarInterpolation.hpp"

namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void finish(AnmView s,u32 n,AnmTimerHost& host){
    if(!(s.get(0x24)&1)){s.put(0x20,host.global_rate_token());s.put(0x24,s.get(0x24)|1);}
    s.put(0x14,n-1);s.put(0x18,n);s.put(0x1c,word(float(signed_word(n))));
}
}
void scalar_reset_timer(AnmView s,AnmTimerHost& host){finish(s,0,host);}
bool scalar_interpolate(AnmView s,AnmTimerHost& host,float& result){
    i32 duration=signed_word(s.get(0x28));const i32 mode=signed_word(s.get(0x2c));
    if(duration>0){
        const u32 token=s.get(0x20),current=s.get(0x18);float rate=1.f;
        if(token&&!host.timer_rate(token,rate))return false;s.put(0x14,current);
        if(token&&!(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae))){
            const float elapsed=s.floating(0x1c)+rate;s.put(0x18,truncate(elapsed));s.put(0x1c,word(elapsed));
        }else{s.put(0x18,current+1);s.put(0x1c,word(s.floating(0x1c)+1.f));}
        if(signed_word(s.get(0x18))>=duration){finish(s,u32(duration),host);s.put(0x28,0);duration=0;}
    }
    if(!duration){result=s.floating(mode==7||mode==17?0:4);return true;}
    if(mode==7||mode==17){
        result=s.floating(mode==7?4:12)+s.floating(0);s.put(0,word(result));
        if(mode==17)s.put(12,word(s.floating(4)+s.floating(12)));
    }else if(mode==8){
        const float t=s.floating(0x1c)/float(duration),one=1.f-t,a=t-1.f,b=t*2.f;
        const float from=(one*one)*t,to=(a*t)*t,start=(a*a)*(b+1.f),target=(3.f-b)*(t*t);
        result=target*s.floating(4)+start*s.floating(0);result+=from*s.floating(8);result+=to*s.floating(12);
    }else{
        float factor;if(!anm_easing(mode,s.floating(0x1c),float(duration),factor))return false;
        result=s.floating(0)+(s.floating(4)-s.floating(0))*factor;
    }
    s.put(0x10,word(result));return true;
}
}
