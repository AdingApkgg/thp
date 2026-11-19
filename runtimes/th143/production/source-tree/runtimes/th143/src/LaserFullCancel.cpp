#include "LaserFullCancel.hpp"
namespace th143 {
bool cancel_lasers_full(u32 manager,i32 kind,bool items,LaserFullCancelHost& host,i32& result,u32 budget){
 u32 beam;if(!host.laser_full_read(manager+0x18,&beam,4))return false;
 while(beam){if(!budget--)return false;u32 mode,next;if(!host.laser_full_read(beam+0x10,&mode,4)||!host.laser_full_read(beam+8,&next,4))return false;
  if(mode!=1){i32 ignored;if(!host.laser_full_virtual(beam,kind,items,ignored))return false;}beam=next;
 }result=1;return true;
}
}
