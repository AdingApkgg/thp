#include "LaserKind2Points.hpp"
#include <vector>
namespace th143 {
bool refresh_laser_kind2_points(AnmView v,u32 token,LaserKind2PointHost& host){
 const i32 count=signed_word(v.get(0x5e0));if(count<=0)return true;if(count>4096)return false;
 const u32 buffer=v.get(0x14ac);std::vector<u8> points(u32(count)*32);if(!host.laser_point_read(buffer,points.data(),u32(points.size())))return false;
 bool sampled=false;
 for(i32 i=0;i<count;++i){
  AnmView point{points.data()+u32(i)*32};const float time=v.floating(0x48)-float(i);
  if(time<0.f){for(u32 j=0;j<3;++j){point.put(j*4,v.get(0x5c0+j*4));point.put(0xc+j*4,0);}point.put(0x18,v.get(0x5cc));point.put(0x1c,v.get(0x5d4));continue;}
  u32 node=token+0x14b4;std::array<u8,0x3c> bytes{};bool found=false;
  for(u32 steps=0;node;++steps){if(steps>=4096)return false;if(node==token+0x14b4)std::memcpy(bytes.data(),v.data+0x14b4,bytes.size());else if(!host.laser_point_read(node,bytes.data(),u32(bytes.size())))return false;AnmView path{bytes.data()};if(time>=path.floating(8)&&path.floating(0xc)>time){found=true;break;}node=path.get(0);}
  if(!found){sampled=true;continue;}
  LaserPathPoint out{{point.floating(0),point.floating(4),point.floating(8)},point.floating(0x1c),point.floating(0x18)};
  if(!sampled){if(!laser_path_point({bytes.data()},time,out))return false;sampled=true;}
  else {if(!i)return false;AnmView previous{points.data()+u32(i-1)*32};const LaserPathPoint prior{{previous.floating(0),previous.floating(4),previous.floating(8)},previous.floating(0x1c),previous.floating(0x18)};if(!laser_path_previous({bytes.data()},prior,time,out))return false;}
  for(u32 j=0;j<3;++j)point.put(j*4,word(out.position[j]));point.put(0x18,word(out.angle));point.put(0x1c,word(out.speed));
 }
 return host.laser_point_write(buffer,points.data(),u32(points.size()));
}
}
