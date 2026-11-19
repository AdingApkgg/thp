#include "AnmPositionInterpolationBegin.hpp"
namespace th143 {
void begin_anm_position_interpolation(AnmView vm,u32 duration,u32 mode,const std::array<u32,3>& from,const std::array<u32,3>& to,const std::array<u32,3>& zero){
 vm.put(0xec,duration);for(u32 i=0;i<3;++i)vm.put(0xb4+i*4,zero[i]);for(u32 i=0;i<3;++i)vm.put(0xc0+i*4,zero[i]);vm.put(0xf0,mode);
 for(u32 i=0;i<3;++i)vm.put(0x9c+i*4,from[i]);for(u32 i=0;i<3;++i)vm.put(0xa8+i*4,to[i]);const u32 flags=vm.get(0xe8);if(!(flags&1)){vm.put(0xe4,0x4e40b0);vm.put(0xe8,flags|1);}vm.put(0xd8,0xffffffff);vm.put(0xdc,0);vm.put(0xe0,0);
}
}
