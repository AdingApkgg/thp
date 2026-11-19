#include "LaserKind2PolarPath.hpp"
#include "LaserPathSegment.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
bool load_node(u32 p,std::array<u8,0x3c>& out,LaserCurveNodeHost& h){return h.laser_node_read(p,out.data(),u32(out.size()));}
bool seed_path_node(u32 token,u32 type,LaserCurveNodeHost& host){
 std::array<u8,0x3c> bytes{},previous{};if(!load_node(token,bytes,host))return false;AnmView node{bytes.data()};
 node.put(0x10,type);if(!load_node(node.get(4),previous,host))return false;AnmView prior{previous.data()};
 LaserPathPoint p{{node.floating(0x20),node.floating(0x24),node.floating(0x28)},node.floating(0x30),node.floating(0x2c)};
 if(!laser_path_point(prior,prior.floating(0xc),p))return false;
 for(u32 i=0;i<3;++i)node.put(0x20+i*4,word(p.position[i]));node.put(0x2c,word(p.angle));node.put(0x30,word(p.speed));
 DirectionVector direction;if(!direction_vector(p.angle,1.f,direction))return false;node.put(0x28,0);node.put(0x14,word(direction.x));node.put(0x18,word(direction.y));node.put(0x1c,0);
 return host.laser_node_write(token,bytes.data(),u32(bytes.size()));
}
}
bool activate_laser_kind2_polar_path(AnmView v,u32 token,LaserCurveNodeHost& host){
 const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;const u32 row=0x5ec+u32(cursor)*0x2c,type=v.get(row+0x20),flags=v.get(0x598);
 if(!type||(!v.get(row+0x24)&&flags)||(type&flags))return true;if(type!=8)return false;
 const float start=float(signed_word(v.get(row+0x14)));u32 path;
 if(!append_laser_curve_node(token+0x14b4,word(start),host,path)||!seed_path_node(path,2,host))return false;
 const u32 acceleration=v.get(row),turn=v.get(row+4);if(!host.laser_node_write(path+0x34,&acceleration,4)||!host.laser_node_write(path+0x38,&turn,4))return false;
 const i32 duration=signed_word(v.get(row+0x10));const u32 forever=0x497423f0;
 if(duration<0){if(!host.laser_node_write(path+0xc,&forever,4))return false;}
 else {const float end=start+float(duration);const u32 end_bits=word(end);if(!host.laser_node_write(path+0xc,&end_bits,4))return false;u32 constant;if(!append_laser_curve_node(token+0x14b4,word(end),host,constant)||!seed_path_node(constant,0,host)||!host.laser_node_write(constant+0xc,&forever,4))return false;}
 v.put(0x594,u32(cursor)+1);return true;
}
}
