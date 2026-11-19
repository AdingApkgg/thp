#include "LaserKind2CircleCancel.hpp"
#include <vector>
namespace th143 {
bool cancel_laser_kind2_circle(AnmView v,const std::array<float,3>& position,float radius,i32 kind,bool items,LaserKind2RectangleCancelHost& host,i32& result){
 if(!v.data)return false;result=0;if(items&&v.get(0x5b4))return true;
 const i32 initial=signed_word(v.get(0x5e0));if(initial<0||initial>256)return false;
 std::array<u8,256> mask{};const u32 points=v.get(0x14ac);const float rr=radius*radius;
 for(i32 i=0;i<signed_word(v.get(0x5e0));++i){
  if(i>=initial)return false;std::array<float,3> p;if(!host.laser_point_read(points+u32(i)*32,p.data(),12))return false;
  const float dx=position[0]-p[0],dy=position[1]-p[1],distance=dx*dx+dy*dy;if(distance>rr)continue;
  ++result;mask[i]=1;if(i%3==0&&(!host.laser_rectangle_item(p,kind)||!host.laser_rectangle_visual(i32(v.get(0x5dc)*3+0xb5u),p)))return false;
 }
 if(!result)return true;const i32 count=signed_word(v.get(0x5e0));if(result>=count){v.put(0xc,(v.get(0xc)&~4u)|2u);return true;}
 auto trim=[&](i32 begin){const u32 bytes=u32(count-begin)*32;std::vector<u8> data(bytes);if(bytes&&(!host.laser_point_read(points+u32(begin)*32,data.data(),bytes)||!host.laser_point_write(points,data.data(),bytes)))return false;v.put(0x5e0,u32(count-begin));return true;};
 i32 cursor=0;while(cursor<count&&mask[cursor])++cursor;if(cursor)return trim(cursor);
 i32 retained=0;while(cursor<count&&!mask[cursor]){++cursor;++retained;}
 if(cursor>=count||!retained)return true;
 while(cursor<count&&mask[cursor])++cursor;
 if(cursor>=count){v.put(0x5e0,u32(retained));return true;}
 return trim(cursor);
}
}
