#include "LaserKind2Vertices.hpp"
#include "DirectionVector.hpp"
#include <vector>
namespace th143 {
namespace {
float wrap(float value){const float pi=real(0x40490fdb),tau=real(0x40c90fdb);u32 count=0;while(value>pi){value-=tau;if(count++>32)break;}while(real(0xc0490fdb)>value){value+=tau;if(count++>32)break;}return value;}
float side_angle(float angle,float previous,bool first,bool right){
 const float half=real(0x3fc90fdb);const float current=wrap(right?angle-half:angle+half);if(first)return current;
 const float before=wrap(right?previous-half:previous+half),pi=real(0x40490fdb),tau=real(0x40c90fdb);float delta=before-current;
 if(delta>pi)delta=before-(current+tau);else if(current-before>pi)delta=before-(current-tau);
 delta=wrap(delta);delta=wrap(delta*.5f);return wrap(delta+current);
}
}
bool make_laser_kind2_vertices(AnmView v,const std::array<i32,2>& origin,LaserKind2PointHost& host){
 const i32 count=signed_word(v.get(0x5e0));if(count<=0)return true;if(count>4096)return false;
 std::vector<u8> points(u32(count)*32),vertices(u32(count)*56);if(!host.laser_point_read(v.get(0x14ac),points.data(),u32(points.size())))return false;
 float u=0.f;for(i32 i=0;i<count;++i){AnmView point{points.data()+u32(i)*32};const float angle=point.floating(0x18),previous=i?AnmView{points.data()+u32(i-1)*32}.floating(0x18):0.f;
  for(u32 side=0;side<2;++side){AnmView vertex{vertices.data()+u32(i)*56+side*28};DirectionVector offset;if(!direction_vector(side_angle(angle,previous,!i,side!=0),v.floating(0x5d0)*.5f,offset))return false;
   const float x=point.floating(0)+offset.x,y=point.floating(4)+offset.y;
   vertex.put(0,word(float(origin[0])+x));vertex.put(4,word(float(origin[1])+y));vertex.put(8,0);vertex.put(12,0x3f800000);vertex.put(16,0xffffffff);vertex.put(20,word(u));vertex.put(24,v.get(side?0xce0:0xcd0));
  }
  if(i+1<count)u=1.f/float(count-1)+u;
 }
 return host.laser_point_write(v.get(0x14b0),vertices.data(),u32(vertices.size()));
}
}
