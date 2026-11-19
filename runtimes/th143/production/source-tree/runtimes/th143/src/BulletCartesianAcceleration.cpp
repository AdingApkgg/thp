#include "BulletCartesianAcceleration.hpp"
#include "DirectionVector.hpp"
#include <cmath>
#include <map>
namespace th143 {
namespace {
struct Services {std::function<bool(BulletView,float&)> aim;std::function<bool(i32)> sound;};
std::map<BulletMotionHost*,Services> services;
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
}
void bind_bullet_cartesian_services(BulletMotionHost& h,std::function<bool(BulletView,float&)> aim,std::function<bool(i32)> sound){if(aim||sound)services[&h]={std::move(aim),std::move(sound)};else services.erase(&h);}
bool start_bullet_cartesian_acceleration(BulletView b,u32 row,BulletMotionHost& h,u32 rate){
 b.put(0xc04,b.get(0xc04)|4u);b.put(0xf9c,b.get(row));float angle=b.floating(row+4);
 if(angle<=-990.f)angle=b.floating(0xbdc);else{if(angle>=990.f){auto s=services.find(&h);if(s==services.end()||!s->second.aim||!s->second.aim(b,angle))return false;angle+=b.floating(row+8);}angle=wrap(angle);}
 b.put(0xfa0,word(angle));if(!(b.get(0xf98)&1)){b.put(0xf94,rate);b.put(0xf98,b.get(0xf98)|1);}b.put(0xf88,0xffffffff);b.put(0xf8c,0);b.put(0xf90,0);b.put(0xfbc,b.get(row+0x10));
 DirectionVector v;if(!direction_vector(angle,b.floating(0xf9c),v))return false;b.put(0xfb0,word(v.x));b.put(0xfb4,word(v.y));
 if(b.get(0xc20)&&signed_word(b.get(0xc1c))>=0){auto s=services.find(&h);if(s==services.end()||!s->second.sound||!s->second.sound(signed_word(b.get(0xc1c))))return false;}return true;
}
i32 bullet_cartesian_acceleration(BulletView b,BulletMotionHost& h){
 if(signed_word(b.get(0xf8c))>=signed_word(b.get(0xfbc))){b.put(0xc04,b.get(0xc04)&~4u);return 1;}
 float rate;if(!h.timer_rate(0x4e40b0,rate))return -2;b.put(0xbd8,word(b.floating(0xf9c)*rate+b.floating(0xbd8)));
 for(u32 i=0;i<3;++i)b.put(0xbcc+i*4,word(b.floating(0xbcc+i*4)+b.floating(0xfb0+i*4)*rate));
 const float x=b.floating(0xbcc),y=b.floating(0xbd0);if(std::fabs(x)>real(0x38d1b717)||std::fabs(y)>real(0x38d1b717)){b.put(0xbdc,word(wrap(float(std::atan2(double(y),double(x))))));const float xx=x*x,yy=y*y;b.put(0xbd8,word(float(std::sqrt(double(xx+yy)))));}
 const u32 pointer=b.get(0xf94),old=b.get(0xf8c);float timer_rate=1;if(pointer&&!h.timer_rate(pointer,timer_rate))return -2;const bool unit=!pointer||(timer_rate>real(0x3f7d70a4)&&timer_rate<real(0x3f8147ae));const float value=b.floating(0xf90)+(unit?1.f:timer_rate);b.put(0xf88,old);b.put(0xf8c,unit?old+1:truncate(value));b.put(0xf90,word(value));return 0;
}
}
