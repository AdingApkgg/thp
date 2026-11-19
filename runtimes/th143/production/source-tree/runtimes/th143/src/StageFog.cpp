#include "StageFog.hpp"

namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void pack(std::array<u32,7>& value){u32 color=0;for(u32 i=0;i<4;++i)color|=u32(u8(truncate(real(value[i+2]))))<<(i*8);value[6]=color;}
std::array<u32,7> load(AnmView s,u32 p){std::array<u32,7> out;for(u32 i=0;i<7;++i)out[i]=s.get(p+i*4);return out;}
void store(AnmView s,u32 p,const std::array<u32,7>& v){for(u32 i=0;i<7;++i)s.put(p+i*4,v[i]);}
bool advance(AnmView t,AnmTimerHost& h){
    const u32 current=t.get(4),pointer=t.get(12);float rate=1;if(pointer&&!h.timer_rate(pointer,rate))return false;
    const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float elapsed=t.floating(8)+(unit?1.f:rate);
    t.put(0,current);t.put(4,unit?current+1:truncate(elapsed));t.put(8,word(elapsed));return true;
}
void set_timer(AnmView t,u32 value,u32 rate){if(!(t.get(16)&1)){t.put(12,rate);t.put(16,t.get(16)|1);}t.put(0,value-1);t.put(4,value);t.put(8,word(float(signed_word(value))));}
}
void stage_fog_begin(AnmView s,const std::array<u32,7>& start,const std::array<u32,7>& target,u32 duration,u32 mode,u32 rate){store(s,0,start);store(s,0x1c,target);s.put(0xa0,duration);s.put(0xa4,mode);set_timer(s.sub(0x8c),0,rate);}
bool stage_fog_interpolate(AnmView s,AnmTimerHost& host,std::array<u32,7>& out){
    i32 duration=signed_word(s.get(0xa0));const i32 mode=signed_word(s.get(0xa4));
    if(duration>0){if(!advance(s.sub(0x8c),host))return false;if(signed_word(s.get(0x90))>=duration){set_timer(s.sub(0x8c),u32(duration),host.global_rate_token());s.put(0xa0,0);duration=0;}}
    if(!duration){out=load(s,mode==7||mode==17?0:0x1c);return true;}
    const auto start=load(s,0),target=load(s,0x1c),from=load(s,0x38),to=load(s,0x54);
    float fraction=0,a=0,b=0,c=0,d=0;
    if(mode==8){const float t=s.floating(0x94)/float(duration),minus=t-1.f,twice=t*2.f,one_minus=1.f-t;a=(minus*minus)*(twice+1.f);b=(3.f-twice)*(t*t);c=(one_minus*one_minus)*t;d=(minus*t)*t;}
    else if(mode!=7&&mode!=17&&!anm_easing(mode,s.floating(0x94),float(duration),fraction))return false;
    for(u32 i=0;i<6;++i){float value;
        if(mode==7)value=real(target[i])+real(start[i]);
        else if(mode==17)value=real(to[i])+real(start[i]);
        else if(mode==8){value=real(start[i])*a+real(target[i])*b;value+=real(from[i])*c;value+=real(to[i])*d;}
        else{value=(real(target[i])-real(start[i]))*fraction;value+=real(start[i]);}
        out[i]=word(value);
    }pack(out);
    if(mode==7||mode==17){store(s,0,out);if(mode==17){auto velocity=to;for(u32 i=0;i<6;++i)velocity[i]=word(real(target[i])+real(to[i]));pack(velocity);store(s,0x54,velocity);}}
    store(s,0x70,out);return true;
}
}
