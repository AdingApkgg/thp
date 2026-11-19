#include "BulletDirectionChange.hpp"
#include "DirectionVector.hpp"
#include <cmath>
#include <map>
namespace th143 {
namespace {
std::map<BulletMotionHost*,BulletDirectionServices> services;
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
void reset(BulletView b,u32 rate){if(!(b.get(0x1028)&1)){b.put(0x1024,rate);b.put(0x1028,b.get(0x1028)|1);}b.put(0x1018,0xffffffff);b.put(0x101c,0);b.put(0x1020,0);}
bool aim(BulletView b,u32 at,BulletDirectionServices& s,float& a){return s.aim&&s.aim({b.floating(at),b.floating(at+4),b.floating(at+8)},a);}
u32 truncate(float a){return a>=-2147483648.f&&a<2147483648.f?u32(i32(a)):0x80000000;}
bool velocity(float angle,float speed,DirectionVector& v){if(!std::isfinite(angle)||std::fabs(angle)>real(0x43c90fdb))return false;v.x=float(std::cos(double(angle))*double(speed));v.y=float(std::sin(double(angle))*double(speed));return true;}
}
void bind_bullet_direction_change(BulletMotionHost& h,BulletDirectionServices s){if(s.random||s.aim||s.sound)services[&h]=std::move(s);else services.erase(&h);}
bool start_bullet_direction_change(BulletView b,u32 row,BulletMotionHost& h,u32 rate){
 auto found=services.find(&h);BulletDirectionServices none;auto& s=found==services.end()?none:found->second;b.put(0xc04,b.get(0xc04)|16u);const u32 mode=b.get(row+0x18);float angle=b.floating(row);
 switch(mode){
 case 0:if(angle<=-990.f)angle=b.floating(0xbdc);else{if(angle>=990.f&&!aim(b,0xbc0,s,angle))return false;angle=wrap(angle);}b.put(0x1030,word(angle));break;
 case 1:case 4:b.put(0x1030,b.get(row));break;
 case 2:{float a;if(!aim(b,0x12bc,s,a))return false;b.put(0x1030,word(wrap(a+angle)));break;}
 case 3:b.put(0x1030,word(wrap(b.floating(0x12b8)+angle)));break;
 case 6:if(!s.random)return false;b.put(0x1030,word(s.random->signed_unit()*angle));break;
 case 5:{if(!s.random)return false;if(angle<=-990.f)angle=wrap(b.floating(0xbdc)+s.random->signed_unit()*angle);else if(angle>=990.f){float a;if(!aim(b,0xbc0,s,a))return false;angle=wrap(a+s.random->signed_unit()*angle);}else angle=wrap(s.random->signed_unit()*angle);b.put(0x1030,word(angle));break;}
 }
 const float speed=b.floating(row+4);b.put(0x102c,speed>-999.f?b.get(row+4):b.get(0xbd8));reset(b,rate);b.put(0x104c,b.get(row+0x10));b.put(0x1050,b.get(row+0x14));b.put(0x1054,0);b.put(0x1058,mode);b.put(0x105c,b.get(row+0x1c));return true;
}
i32 bullet_direction_change(BulletView b,BulletMotionHost& h){
 float speed=b.floating(0xbd8);if(signed_word(b.get(0x101c))>=signed_word(b.get(0x104c))){
  auto found=services.find(&h);BulletDirectionServices none;auto& s=found==services.end()?none:found->second;if(signed_word(b.get(0xc1c))>=0&&(!s.sound||!s.sound(signed_word(b.get(0xc1c)))))return -2;
  b.put(0x1054,b.get(0x1054)+1);float angle=b.floating(0x1030);switch(b.get(0x1058)){case 0:case 5:b.put(0xbdc,word(wrap(b.floating(0xbdc)+angle)));break;case 1:case 6:{float a;if(!aim(b,0xbc0,s,a))return -2;b.put(0xbdc,word(wrap(a+angle)));break;}case 2:{float a;if(!aim(b,0x12bc,s,a))return -2;b.put(0xbdc,word(wrap(a+angle)));break;}case 3:b.put(0xbdc,word(wrap(b.floating(0x12b8)+angle)));break;case 4:b.put(0xbdc,word(wrap(angle)));break;}
  speed=b.floating(0x102c);b.put(0xbd8,b.get(0x102c));reset(b,0x4e40b0);if(signed_word(b.get(0x1054))>=signed_word(b.get(0x1050))){DirectionVector v;if(!velocity(b.floating(0xbdc),speed,v))return -2;b.put(0xbcc,word(v.x));b.put(0xbd0,word(v.y));b.put(0xc04,b.get(0xc04)&~16u);return 1;}
 }else{const float product=b.floating(0x1020)*speed;const float reduction=product/float(signed_word(b.get(0x104c)));speed-=reduction;}
 DirectionVector v;if(!velocity(b.floating(0xbdc),speed,v))return -2;b.put(0xbcc,word(v.x));b.put(0xbd0,word(v.y));const u32 pointer=b.get(0x1024),old=b.get(0x101c);float rate=1;if(pointer&&!h.timer_rate(pointer,rate))return -2;const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=b.floating(0x1020)+(unit?1.f:rate);b.put(0x1018,old);b.put(0x101c,unit?old+1:truncate(value));b.put(0x1020,word(value));return 0;
}
}
