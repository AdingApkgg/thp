#include "LaserKind0FullCancel.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
bool cancel_laser_kind0_full(AnmView v,i32 kind,bool items,LaserKind0RectangleCancelHost& host,i32& result){
 if(!v.data)return false;result=0;if(items&&v.get(0x5b4))return true;
 const float length=v.floating(0x70);if(!std::isfinite(length)||length>4096.f)return false;
 DirectionVector direction;if(!direction_vector(v.floating(0x6c),8.f,direction))return false;
 std::array<float,3> point{v.floating(0x54)+direction.x,v.floating(0x58)+direction.y,v.floating(0x5c)+0.f};
 const std::array<float,3> step{direction.x+direction.x,direction.y+direction.y,0};float distance=8.f;
 if(length>16.f)do{
  ++result;const i32 type=signed_word(v.get(0x5b8)),color=signed_word(v.get(0x5e8));i32 base=0;
  if(type<=17||type==33||type==37)base=0xb5;else if(type<=30)base=0xe5;else if(type<=32)base=0xfd;
  if(base&&!host.laser_rectangle_visual(i32(u32(color)*3+u32(base)),point))return false;
  if(!host.laser_rectangle_item(point,kind))return false;
  distance+=16.f;for(u32 i=0;i<3;++i)point[i]+=step[i];
 }while(length>distance+8.f);
 v.put(0x10,1);return true;
}
}
