#include "LaserKind2Cleanup.hpp"
namespace th143 {
bool cleanup_laser_kind2(AnmView v,LaserKind2CleanupHost& host){
 if(!v.data)return false;u32 node=v.get(0x14b4);
 for(u32 i=0;node;++i){if(i>=4096)return false;u32 next;if(!host.laser_cleanup_read(node,&next,4)||!host.laser_cleanup_release(node,false))return false;node=next;}
 for(u32 i=0;i<2;++i){const u32 at=i?0x14acu:0x14b0u,pointer=v.get(at);if(pointer){if(!host.laser_cleanup_release(pointer,true))return false;v.put(at,0);}}
 return true;
}
}
