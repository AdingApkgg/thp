#include "LaserKind2Draw.hpp"
namespace th143 {
bool draw_laser_kind2(AnmView v,u32 token,const std::array<i32,2>& origin,LaserKind2DrawHost& host){
 if(signed_word(v.get(0x5e0))<1)return false;
 if(!make_laser_kind2_vertices(v,origin,host)||!host.laser_draw_external(token+0x914,v.sub(0x914),v.get(0x14b0),v.get(0x5e0)*2))return false;
 const i32 count=signed_word(v.get(0x5e0));if(count>=signed_word(v.get(0x44))){
  if(count<1||count>4096)return false;std::array<u8,12> position;if(!host.laser_point_read(v.get(0x14ac)+u32(count-1)*32,position.data(),12))return false;
  auto secondary=v.sub(0xee0);std::memcpy(secondary.data+0x3c,position.data(),12);if(!host.laser_draw_secondary(token+0xee0,secondary))return false;
 }
 return true;
}
}
