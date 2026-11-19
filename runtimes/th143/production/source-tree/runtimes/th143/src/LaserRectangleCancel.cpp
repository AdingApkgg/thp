#include "LaserRectangleCancel.hpp"
#include <array>
namespace th143 {
bool cancel_lasers_rectangle(u32 manager,u32 position,u32 size,float angle,LaserRectangleCancelHost& host,i32& result,u32 budget){
 std::array<u32,3> data;u32 beam;
 if(!host.laser_cancel_read(manager+0x18,&beam,4)||!host.laser_cancel_read(position,data.data(),12)||!host.laser_cancel_write(manager+0x5dc,data.data(),12))return false;
 if(!host.laser_cancel_read(size,data.data(),12)||!host.laser_cancel_write(manager+0x5e8,data.data(),12))return false;
 u32 total=0;
 while(beam){
  if(!budget--)return false;u32 mode,next,flags;
  if(!host.laser_cancel_read(beam+0x10,&mode,4)||!host.laser_cancel_read(beam+8,&next,4))return false;
  if(mode!=1){
   if(!host.laser_cancel_read(beam+0xc,&flags,4))return false;
   if(flags&1){i32 count;if(!host.laser_cancel_rectangle_virtual(beam,position,size,angle,count))return false;total+=u32(count);}
  }beam=next;
 }result=signed_word(total);return true;
}
}
