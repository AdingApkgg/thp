#include "LaserCancel.hpp"
#include <array>
namespace th143 {
bool cancel_lasers_circle(u32 manager,u32 position,float radius,i32 kind,bool items,LaserCancelHost& host,i32& result,u32 budget){
    std::array<u32,3> coordinates;u32 beam;
    if(!host.laser_cancel_read(position,coordinates.data(),12)||!host.laser_cancel_read(manager+0x18,&beam,4)||!host.laser_cancel_write(manager+0x5dc,coordinates.data(),12))return false;
    u32 total=0;
    while(beam){
        if(!budget--)return false;u32 mode,next;
        if(!host.laser_cancel_read(beam+0x10,&mode,4)||!host.laser_cancel_read(beam+8,&next,4))return false;
        if(mode!=1){i32 count;if(!host.laser_cancel_virtual(beam,position,radius,kind,items,count))return false;total+=u32(count);}
        beam=next;
    }result=signed_word(total);return true;
}
}
