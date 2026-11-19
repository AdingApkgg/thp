#include "LaserReset.hpp"
namespace th143 {
bool reset_lasers(u32 manager,LaserResetHost& host,i32& result,u32 budget){
 u32 beam;if(!host.laser_full_read(manager+0x18,&beam,4))return false;
 auto write=[&](u32 p,u32 v){return host.laser_reset_write(p,&v,4);};
 while(beam){if(!budget--)return false;u32 flags,next;if(!host.laser_full_read(beam+0x5b0,&flags,4)||!host.laser_full_read(beam+8,&next,4))return false;
  if(!(flags&1)&&(!write(beam+0x5a4,0)||!write(beam+0x5a0,0xfff0bdc1)||!write(beam+0x5a8,0)||!write(beam+0x5ac,0x4e40b0)||!write(beam+0x5b0,flags|1)))return false;
  if(!write(beam+0x5a4,0)||!write(beam+0x5a8,0)||!write(beam+0x5a0,0xffffffff)||!write(beam+0x5b4,0))return false;
  i32 ignored;if(!host.laser_full_virtual(beam,1,false,ignored))return false;beam=next;
 }result=0;return true;
}
}
