#include "LaserKind0Bounce.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
namespace {
// Original4058a0 floating-point order; a/b are the finite boundary segment,
// c/d the beam tip and origin. Parallel lines retain the original guards.
bool intersection(float ax,float ay,float bx,float by,float cx,float cy,float dx,float dy,float& x,float& y){
 const float abx=ax-bx,aby=ay-by;
 const float t1=(cy-ay)*abx+aby*(ax-cx),t2=(ax-dx)*aby+(dy-ay)*abx;
 if(t1*t2>0.f)return false;
 if(t1==0.f&&t2==0.f){
  if(std::max(ax,bx)<std::min(cx,dx)||std::max(ay,by)<std::min(cy,dy)||std::max(cx,dx)<std::min(ax,bx)||std::max(cy,dy)<std::min(ay,by))return false;
 }else{
  const float cdx=cx-dx,cdy=cy-dy;
  const float u1=(cx-ax)*cdy+(ay-cy)*cdx,u2=(cx-bx)*cdy+(by-cy)*cdx;
  if(u1*u2>0.f)return false;
 }
 const float edge_dx=bx-ax;const bool edge_vertical=std::fabs(edge_dx)<real(0x3c23d70a);
 const float edge_dy=by-ay;
 const float slope=edge_vertical?0.f:edge_dy/edge_dx;
 const float intercept=edge_vertical?ax:by-(edge_dy*ax)/edge_dx;
 const float ray_dx=dx-cx;const bool ray_vertical=std::fabs(ray_dx)<real(0x3c23d70a);
 const float ray_dy=dy-cy;
 const float ray_slope=ray_vertical?0.f:ray_dy/ray_dx;
 const float ray_intercept=ray_vertical?cx:cy-(ray_dy*cx)/ray_dx;
 if(edge_vertical){if(ray_vertical){if(!(real(0x3a83126f)>std::fabs(ax-cx)))return false;x=ax;y=ay;}else{x=ax;y=ray_slope*ax+ray_intercept;}}
 else if(ray_vertical){x=cx;y=slope*cx+intercept;}
 else{const float delta=ray_intercept-intercept,denominator=slope-ray_slope;x=delta/denominator;y=(delta*slope)/denominator+intercept;}
 return true;
}
bool sound(AnmView v,LaserKind0BounceServices& h){const i32 id=signed_word(v.get(0x910));return id<0||(h.sound&&h.sound(id));}
}
bool dispatch_laser_kind0_bounce(AnmView v,LaserKind0BounceServices& h){
 if(!v.data)return false;
 for(u32 steps=0;steps<64;++steps){
  const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;
  AnmView row=v.sub(0x5f4+u32(cursor)*0x2c);const u32 type=row.get(0x20);if(!type||(!row.get(0x24)&&v.get(0x598)))return true;
  if(type!=0x40)return false;
  if(signed_word(row.get(0x10))>0&&!(v.get(0x5f0)&2)){
   v.put(0x598,v.get(0x598)|0x40);
   const float speed=row.floating(0);v.put(0x1b8,speed>=0.f?word(speed):v.get(0x78));
   row.put(0x10,row.get(0x10)-1);v.put(0x1dc,row.get(0x10));v.put(0x1d8,0);v.put(0x1e0,row.get(0x14));
  }
  v.put(0x594,u32(cursor)+1);
 }
 return false;
}
bool advance_laser_kind0_bounce(AnmView v,LaserKind0BounceServices& h,i32& result){
 if(!v.data)return false;DirectionVector direction;if(!direction_vector(v.floating(0x6c),v.floating(0x70),direction))return false;
 const float px=v.floating(0x54),py=v.floating(0x58),x=direction.x+px,y=py+direction.y;
 if(x>-192.f&&x<192.f&&y>0.f&&y<448.f){result=0;return true;}
 bool hit=false;
 auto boundary=[&](u32 flag,bool outside,float ax,float ay,float bx,float by,bool vertical)->bool{
  const u32 mask=v.get(0x1e0);if(!(mask&flag)||!outside)return true;hit=true;if(mask&0x10)return true;
  float ix,iy;if(intersection(ax,ay,bx,by,x,y,px,py,ix,iy)){v.put(0x5c0,word(ix));v.put(0x5c4,word(iy));}
  std::array<u8,0x354> parameters;std::memcpy(parameters.data(),v.data+0x5c0,parameters.size());AnmView p{parameters.data()};p.put(8,0);
  float angle=real(v.get(0x6c)^0x80000000u);
  if(vertical){angle-=real(0x40490fdb);u32 wraps=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(wraps++>32)break;}while(angle<real(0xc0490fdb)){angle+=real(0x40c90fdb);if(wraps++>32)break;}}
  p.put(0xc,word(angle));p.put(0x20,v.get(0x1b8));p.put(0x2c,0);
  if(!h.spawn||!h.spawn(parameters.data(),parameters.size()))return false;v.put(0x5f0,v.get(0x5f0)|2);return true;
 };
 if(!boundary(1,y<0.f,-256.f,0.f,256.f,0.f,false)||!boundary(2,y>448.f,-256.f,448.f,256.f,448.f,false)||!boundary(4,x<-192.f,-192.f,-192.f,-192.f,640.f,true)||!boundary(8,x>192.f,192.f,-192.f,192.f,640.f,true))return false;
 if(hit){v.put(0x598,v.get(0x598)&~0x40u);if(!sound(v,h))return false;result=1;}else result=0;
 return true;
}
}
