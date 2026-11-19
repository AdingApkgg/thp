#include "LaserManager.hpp"
namespace th143 {
namespace {
struct Memory {
    LaserManagerHost& host;
    bool read(u32 p,u32& value){return host.laser_read(p,&value,4);}
    bool write(u32 p,u32 value){return host.laser_write(p,&value,4);}
    bool tick(u32 self){
        u32 token,old,bits;if(!read(self+0x24,token)||!read(self+0x1c,old)||!write(self+0x18,old)||!read(self+0x20,bits))return false;
        float rate=1;if(token&&!host.timer_rate(token,rate))return false;
        const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=real(bits)+(unit?1.f:rate);
        return write(self+0x1c,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000)&&write(self+0x20,word(value));
    }
};
}
bool update_laser_manager(u32 self,LaserManagerHost& host,u32 budget){
    Memory m{host};u32 laser;if(!m.read(self+0x18,laser))return false;
    while(laser){
        if(!budget--)return false;u32 flags,next,mode;if(!m.read(laser+0xc,flags)||!m.read(laser+8,next))return false;
        bool destroy=false;
        if(flags&6){flags=(flags&~6u)|(((flags&~1u)+2)&6);if(!m.write(laser+0xc,flags))return false;destroy=(flags&6)>=4;}
        i32 result=0;
        if(!destroy){
            if(!m.read(laser+0x10,mode))return false;destroy=mode==1;
            if(!destroy){
                if(!m.read(laser+0xc,flags))return false;
                if(flags&8){if(!host.laser_virtual(laser,0x34,true,1,result))return false;laser=next;continue;}
                if(!host.laser_virtual(laser,0x10,false,0,result))return false;destroy=result!=0;
            }
        }
        if(destroy){
            if(!host.laser_virtual(laser,0x18,false,0,result))return false;
            u32 count,previous,following,tail;
            if(!m.read(self+0x5d4,count)||!m.write(self+0x5d4,count-1)||!m.read(laser+4,previous)||!m.read(laser+8,following)||!m.write(previous+8,following))return false;
            if(following&&!m.write(following+4,previous))return false;
            if(!m.read(self+0x5d0,tail))return false;if(tail==laser&&!m.write(self+0x5d0,previous))return false;
            if(!host.laser_release(laser))return false;
        }else{
            if(!m.tick(laser)||!m.read(laser+0xc,flags)||!m.write(laser+0xc,flags|1))return false;
        }
        laser=next;
    }return true;
}
bool frame_laser_manager(u32 self,u32 flags,float& rate,LaserManagerHost& host){
    if(flags&0x405)return true;
    const float old=rate;if(flags&2)rate=0;
    const bool result=update_laser_manager(self,host);if(flags&2)rate=old;return result;
}
bool draw_laser_manager(u32 self,LaserManagerHost& host,u32 budget){
    Memory m{host};u32 laser;if(!m.read(self+0x18,laser))return false;
    while(laser){
        if(!budget--)return false;u32 mode,next;
        if(!m.read(laser+0x10,mode)||!m.read(laser+8,next))return false;
        if(mode!=1){i32 result;if(!host.laser_virtual(laser,0x14,false,0,result))return false;}
        laser=next;
    }return true;
}
bool frame_draw_laser_manager(u32 self,u32 flags,LaserManagerHost& host){return (flags&4)||draw_laser_manager(self,host);}
}
