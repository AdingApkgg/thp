#include "LaserKind2FullCancel.hpp"
namespace th143 {
bool cancel_laser_kind2_full(AnmView v,i32,bool items,LaserKind2RectangleCancelHost& host,i32& result){
 if(!v.data)return false;result=0;if(items&&v.get(0x5b4))return true;
 const u32 pointer=v.get(0x14ac);
 for(i32 i=0;i<signed_word(v.get(0x5e0));++i){
  if(i>=4096)return false;std::array<float,3> p;if(!host.laser_point_read(pointer+u32(i)*32,p.data(),12))return false;
  if(i%3==0&&!host.laser_rectangle_visual(i32(v.get(0x5dc)*2+0xb5u),p))return false;
 }
 v.put(0x10,1);return true;
}
}
