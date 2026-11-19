#include "BulletExtended.hpp"
#include "DirectionVector.hpp"
#include <map>
namespace th143 {
namespace {
std::map<BulletMotionHost*,std::function<bool(i32)>> sounds;
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void reset(BulletView b,u32 at,u32 n,u32 rate){if(!(b.get(at+16)&1)){b.put(at+12,rate);b.put(at+16,b.get(at+16)|1);}b.put(at,n-1);b.put(at+4,n);b.put(at+8,word(float(signed_word(n))));}
bool tick(BulletView b,u32 at,BulletMotionHost& h,bool decrement){u32 p=b.get(at+12),old=b.get(at+4);float r=1;if(p&&!h.timer_rate(p,r))return false;const bool unit=!p||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));b.put(at,old);const float v=decrement?b.floating(at+8)-(unit?1.f:r):b.floating(at+8)+(unit?1.f:r);b.put(at+4,decrement||!unit?truncate(v):old+1);b.put(at+8,word(v));return true;}
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
}
void bind_bullet_transform_sound(BulletMotionHost& h,std::function<bool(i32)> f){if(f)sounds[&h]=std::move(f);else sounds.erase(&h);}
bool start_bullet_extended_transform(BulletView b,u32 row,u32 type,BulletMotionHost& h,u32 rate){
 if(type==0x80000000){const i32 n=signed_word(b.get(row+0x10));if(n>0){b.put(0xc04,b.get(0xc04)|type);reset(b,0x10a8,u32(n),rate);}return true;}
 if(type!=8)return false;b.put(0xc04,b.get(0xc04)|8u);b.put(0xfe4,b.get(row));b.put(0xfe8,b.get(row+4));reset(b,0xfd0,0,rate);b.put(0x1004,b.get(row+0x10));
 if(b.get(0xc20)&&signed_word(b.get(0xc1c))>=0){auto i=sounds.find(&h);if(i==sounds.end()||!i->second(signed_word(b.get(0xc1c))))return false;}return true;
}
i32 bullet_polar_acceleration(BulletView b,BulletMotionHost& h){
 if(signed_word(b.get(0xfd4))>=signed_word(b.get(0x1004))){b.put(0xc04,b.get(0xc04)&~8u);return 1;}
 float rate;if(!h.timer_rate(0x4e40b0,rate))return -2;const float angle=wrap(wrap(b.floating(0xfe8)*rate+b.floating(0xbdc))),speed=b.floating(0xfe4)*rate+b.floating(0xbd8);b.put(0xbdc,word(angle));b.put(0xbd8,word(speed));DirectionVector v;if(!direction_vector(angle,speed,v))return -2;b.put(0xbcc,word(v.x));b.put(0xbd0,word(v.y));return tick(b,0xfd0,h,false)?0:-2;
}
i32 bullet_transform_wait(BulletView b,BulletMotionHost& h){if(signed_word(b.get(0x10ac))<=0){b.put(0xc04,b.get(0xc04)^0x80000000u);return 1;}return tick(b,0x10a8,h,true)?0:-2;}
}
