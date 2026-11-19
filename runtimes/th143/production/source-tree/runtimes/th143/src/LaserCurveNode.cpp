#include "LaserCurveNode.hpp"
namespace th143 {
bool append_laser_curve_node(u32 root,u32 time,LaserCurveNodeHost& host,u32& result){
 u32 last=root,next=0;if(!host.laser_node_read(last,&next,4))return false;
 for(u32 steps=0;next;++steps){if(steps>=4096)return false;last=next;if(!host.laser_node_read(last,&next,4))return false;}
 u32 token;u8* bytes;if(!host.laser_node_allocate(0x3c,token,bytes)||!token||!bytes)return false;
 if(!host.laser_node_write(last,&token,4)||!host.laser_node_write(last+12,&time,4))return false;
 AnmView node{bytes};node.put(8,time);node.put(0,0);node.put(4,last);result=token;return true;
}
}
