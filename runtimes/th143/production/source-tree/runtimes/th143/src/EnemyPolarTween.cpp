#include "EnemyPolarTween.hpp"
#include <cmath>
namespace th143 {
namespace {
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
float mirror(float a){const float half=real(0x3fc90fdb);return wrap(half-wrap(a-half));}
}
bool set_enemy_polar(ActorState& s,bool relative,float angle,float speed){
 const u32 base=relative?0xcc:0x88;
 if(double(angle)>-999999.)s.put(base+0x1c,word(wrap(s.get(0x4100)&0x80000?mirror(angle):angle)));
 if(double(speed)>-999999.)s.put(base+0x18,word(speed));s.put(base+0x40,s.get(base+0x40)&~15u);return true;
}
bool start_enemy_polar_tween(ActorState& s,bool relative,i32 duration,i32 mode,float angle,float speed,AnmTimerHost& host){
 const u32 base=relative?0xcc:0x88,a=relative?0x4cc:0x46c,v=a+0x30;
 if(duration<=0){s.put(a+0x28,0);s.put(v+0x28,0);return true;}
 if(mode==7){angle=double(angle)>-999999.?(s.get(0x4100)&0x80000?-angle:angle):0.f;speed=double(speed)>-999999.?speed:0.f;}
 else {angle=double(angle)>-999999.?(s.get(0x4100)&0x80000?mirror(angle):angle):s.fields.floating(base+0x1c);if(!(double(speed)>-999999.))speed=s.fields.floating(base+0x18);}
 float from=s.fields.floating(base+0x1c);
 if(!(std::fabs(from-angle)<real(0x40490fdb))){if(angle>from)from+=real(0x40c90fdb);else angle+=real(0x40c90fdb);}
 for(u32 at:{a,v}){s.put(at+0x28,u32(duration));s.put(at+0x2c,u32(mode));s.put(at+8,0);s.put(at+12,0);scalar_reset_timer({s.fields.data.data()+at},host);}
 s.put(a,word(from));s.put(a+4,word(angle));s.put(v, s.get(base+0x18));s.put(v+4,word(speed));s.put(base+0x40,s.get(base+0x40)&~15u);return true;
}
}
