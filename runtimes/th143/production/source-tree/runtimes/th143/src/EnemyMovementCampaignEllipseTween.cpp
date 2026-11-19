#include "EnemyEllipsePair.hpp"
#include "EnemyEllipseAdvance.hpp"
#include "EnemyMovementShooting.hpp"
#include "DirectionVector.hpp"
#include <cmath>

namespace th143 {
float enemy_position_quantize(float value){return float(std::floor(double(value*100.f)))/100.f;}
namespace {
float wrap(float a){
    const float pi=real(0x40490fdb),tau=real(0x40c90fdb);u32 i=0;
    while(a>pi){a-=tau;if(i++>32)break;}
    while(a<-pi){a+=tau;if(i++>32)break;}return a;
}
}
bool enemy_random_movement(ActorState& s,bool relative,i32 duration,i32 mode,float speed,float aim_x,Rng& rng,AnmTimerHost& host){
    const float x=s.fields.floating(0x44),y=s.fields.floating(0x48),cx=s.fields.floating(0x4004),cy=s.fields.floating(0x4008);
    const float hx=s.fields.floating(0x400c)*.25f,hy=s.fields.floating(0x4010)*.25f,pi=real(0x40490fdb);
    float angle;
    if(cx-hx>x)angle=(rng.signed_unit()*pi)/3.f;
    else if(x>cx+hx)angle=wrap((rng.signed_unit()*pi)/3.f+pi);
    else{
        angle=(rng.signed_unit()*pi)*.25f;const u32 choice=rng.next16()%3;
        if(aim_x>x?choice==0:choice!=0)angle+=pi;
    }
    if(cy-hy>y)angle=std::fabs(angle);else if(y>cy+hy)angle=-std::fabs(angle);
    const float half=real(0x3fc90fdb);
    if(std::fabs(angle+half)<real(0x3d4ccccd))angle=angle<-half?real(0xbfcf7641):real(0xbfc2a975);
    else if(double(std::fabs(angle-half))<.05)angle=angle<half?real(0x3fc2a975):real(0x3fcf7641);
    const u32 a=relative?0x4cc:0x46c,v=relative?0x4fc:0x49c;
    for(const u32 at:{a,v}){s.put(at+8,0);s.put(at+12,0);s.put(at+0x28,u32(duration));scalar_reset_timer({s.fields.data.data()+at},host);}
    s.put(a,word(angle));s.put(a+4,word(angle));s.put(a+0x2c,u32(mode));
    s.put(v,word(speed));s.put(v+4,0);
    // Native42418f writes the angle mode again; speed mode is preserved.
    const u32 position=relative?0xcc:0x88;s.put(position+0x40,s.get(position+0x40)&~15u);return true;
}
bool enemy_direct_movement(ActorState& s,float elapsed,AnmTimerHost& host){

    if(((s.get(0xc8)&15)&&(s.get(0xc8)&15)!=3)||((s.get(0x10c)&15)&&(s.get(0x10c)&15)!=3)||(s.get(0x4100)&0x4000000))return false;
    for(const u32 base:{0x88u,0xccu}){
        const u32 angle=base==0x88?0x46c:0x4cc,speed=angle+0x30;
        if(s.get(angle+0x28)&&(s.get(base+0x40)&15)!=3){
            float value;if(!scalar_interpolate({s.fields.data.data()+angle},host,value))return false;
            s.put(base+0x1c,word(wrap(wrap(value))));
        }
        if(s.get(speed+0x28)){
            float value;if(!scalar_interpolate({s.fields.data.data()+speed},host,value))return false;s.put(base+0x18,word(value));
        }
        const u32 radius=base==0x88?0x52c:0x570;if(s.get(radius+0x3c)){std::array<u32,2> value;if(!sample_enemy_ellipse_pair({s.fields.data.data()+radius},host,value))return false;s.put(base+0x20,value[0]);s.put(base+0x24,value[1]);}
        const u32 tween=base==0x88?0x39c:0x404;
        if((s.get(base+0x40)&15)==3){if(s.get(tween+0x50)||!advance_enemy_ellipse({s.fields.data.data()+base},elapsed))return false;continue;}
        if(s.get(tween+0x50)){std::array<u32,3> value;if(!sample_enemy_position_tween({s.fields.data.data()+tween},host,value))return false;for(u32 i=0;i<3;++i)s.put(base+0x34+i*4,word(real(value[i])-s.fields.floating(base+i*4)));}
        else{DirectionVector v;if(!direction_vector(s.fields.floating(base+0x1c),s.fields.floating(base+0x18)*elapsed,v))return false;s.put(base+0x34,word(v.x));s.put(base+0x38,word(v.y));}
        for(u32 i=0;i<3;++i)s.put(base+i*4,word(s.fields.floating(base+i*4)+s.fields.floating(base+0x34+i*4)));
        for(u32 i=0;i<2;++i)s.put(base+i*4,word(enemy_position_quantize(s.fields.floating(base+i*4))));
    }
    return true;
}
}
