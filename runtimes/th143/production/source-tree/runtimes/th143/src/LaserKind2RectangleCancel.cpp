#include "LaserKind2RectangleCancel.hpp"
#include <cmath>
namespace th143 {
bool cancel_laser_kind2_rectangle(AnmView v,u32 token,const std::array<float,3>& position,const std::array<float,3>& size,float angle,i32 kind,bool items,LaserKind2RectangleCancelHost& host,i32& result){
 if(!v.data)return false;result=0;if(items&&v.get(0x5b4))return true;
 const i32 initial=signed_word(v.get(0x5e0));if(initial<0||initial>4096)return false;
 u32 mask_token;u8* mask;if(!host.laser_rectangle_mask_allocate(u32(initial),mask_token,mask)||!mask)return false;
 std::memset(mask,0,u32(initial));
 auto finish=[&](bool ok){return host.laser_rectangle_mask_release(mask_token)&&ok;};
 const u32 points=v.get(0x14ac);
 for(i32 i=0;i<signed_word(v.get(0x5e0));++i){
  if(i>=initial)return finish(false);
  std::array<float,3> p;if(!host.laser_point_read(points+u32(i)*32,p.data(),12))return finish(false);
  float x=p[0]-position[0],y=p[1]-position[1];
  if(angle!=0.f){const float sine=float(std::sin(double(-angle))),cosine=float(std::cos(double(-angle)));const float a=cosine*x-sine*y,b=cosine*y+sine*x;x=a;y=b;}
  if(!(size[0]*.5f>=std::fabs(x)&&size[1]*.5f>=std::fabs(y)))continue;
  mask[i]=1;++result;
  if(i%3==0&&(!host.laser_rectangle_item(p,kind)||!host.laser_rectangle_visual(i32(v.get(0x5dc)*3+0xb5u),p)))return finish(false);
 }
 auto retire=[&](){v.put(0xc,(v.get(0xc)&~4u)|2u);};
 if(!result)return finish(true);
 i32 count=signed_word(v.get(0x5e0));if(result>=count){retire();return finish(true);}
 i32 cursor=0;while(cursor<count&&mask[cursor])++cursor;
 if(cursor){
  std::memmove(mask,mask+cursor,u32(count-cursor));const u32 prior=v.get(0x44);const float next=v.floating(0x48)-float(cursor);
  v.put(0x40,prior);v.put(0x48,word(next));v.put(0x44,next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000u);
  count-=cursor;v.put(0x5e0,u32(count));if(count<4){retire();return finish(true);}cursor=0;
 }
 while(cursor<count&&!mask[cursor])++cursor;const i32 retained=cursor;
 while(cursor<count){
  while(cursor<count&&mask[cursor])++cursor;const i32 begin=cursor;while(cursor<count&&!mask[cursor])++cursor;const i32 run=cursor-begin;
  if(run>=4){
   std::array<u8,0x354> parameters;std::memcpy(parameters.data(),v.data+0x5c0,parameters.size());AnmView out{parameters.data()};
   out.put(0x344,0xffffffffu);out.put(0x20,u32(run));out.put(0x34c,token+0x14b4);out.put(0x350,word(v.floating(0x48)-float(begin)));
   if(!host.laser_rectangle_spawn(parameters.data(),u32(parameters.size())))return finish(false);
  }
 }
 if(retained>=4)v.put(0x5e0,u32(retained));else retire();return finish(true);
}
}
