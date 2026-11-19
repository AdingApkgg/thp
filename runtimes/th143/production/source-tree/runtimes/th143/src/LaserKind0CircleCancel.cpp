#include "LaserKind0CircleCancel.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
bool cancel_laser_kind0_circle(AnmView v,const std::array<float,3>& p,float radius,i32 kind,bool items,LaserKind0RectangleCancelHost& host,i32& result){
 if(!v.data)return false;result=0;if(items&&v.get(0x5b4))return true;
 const float length=v.floating(0x70);if(!std::isfinite(length)||length>4096.f)return false;
 const std::array<float,3> original{v.floating(0x54),v.floating(0x58),v.floating(0x5c)};
 DirectionVector world;if(!direction_vector(v.floating(0x6c),8.f,world))return false;
 const std::array<float,3> step{world.x+world.x,world.y+world.y,0};
 float wx=original[0]+world.x,wy=original[1]+world.y,distance=8.f;const float radius_squared=radius*radius;
 std::array<u8,256> mask{};u32 count=0;
 if(length>=16.f)do{
  if(count>=mask.size())return false;
  const float dx=p[0]-wx,dy=p[1]-wy;
  if(!(dx*dx+dy*dy>radius_squared)){
   mask[count]=1;++result;const std::array<float,3> point{wx,wy,0};if(!host.laser_rectangle_item(point,kind))return false;
   const i32 type=signed_word(v.get(0x5b8)),color=signed_word(v.get(0x5e8));i32 base=0;
   if(type<=17||type==33||type==37)base=0xb5;else if(type<=30)base=0xe5;else if(type<=32)base=0xfd;
   if(base&&!host.laser_rectangle_visual(i32(u32(color)*3+u32(base)),point))return false;
  }
  ++count;wx+=step[0];wy+=step[1];distance+=16.f;
 }while(length>=distance+8.f);
 if(!result)return true;
 auto retire=[&](){v.put(0xc,(v.get(0xc)&~4u)|2);};
 if(u32(result)>=count){retire();return true;}
 u32 cursor=0;while(cursor<count&&mask[cursor])++cursor;
 if(cursor){const float n=float(cursor),removed=n*16.f;for(u32 i=0;i<3;++i)v.put(0x54+i*4,word(v.floating(0x54+i*4)+step[i]*n));const float remaining=v.floating(0x70)-removed;v.put(0x70,word(remaining));if(remaining>24.f){v.put(0x5d0,word(remaining));v.put(0x7c,word(removed));}else{retire();return true;}}
 u32 run=0;while(cursor<count&&!mask[cursor]){++cursor;++run;}
 if(cursor>=count)return true;
 const float retained=float(run)*16.f,removed=v.floating(0x70)-retained;v.put(0x70,word(retained));v.put(0x5d0,word(v.floating(0x5d0)-removed));if(24.f>retained)retire();
 while(cursor<count){
  if(mask[cursor]){++cursor;continue;}
  const u32 begin=cursor;run=0;do{++cursor;++run;}while(cursor<count&&!mask[cursor]);
  std::array<u8,0x354> parameters;std::memcpy(parameters.data(),v.data+0x5c0,parameters.size());AnmView out{parameters.data()};const float extent=float(run)*16.f;out.put(0x14,word(extent));out.put(0x10,word(extent));
  if(extent>24.f){for(u32 i=0;i<3;++i)out.put(i*4,word(original[i]+step[i]*float(begin)));if(!host.laser_rectangle_spawn(parameters.data(),parameters.size()))return false;}
 }
 return true;
}
}
