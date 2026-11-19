#include "DeviceJoystickControl.hpp"
namespace th143 {
bool poll_device_joystick(u32 held,DeviceJoystickControlHost& h,u32& result){
 result=held;auto read=[&](u32 p,u32& v){return h.joystick_memory_read(p,&v,4);};auto binding=[&](u32 p,i32& value){u16 v;if(!h.joystick_memory_read(p,&v,2))return false;value=v&0x8000?i32(v)-65536:i32(v);return true;};u32 config,status;if(!read(0x4e4ef4,config))return false;
 constexpr u32 addresses[]={0x4e1c04,0x4e1c06,0x4e1c0a,0x4e1c08},masks[]={1,2,0x100,8};
 if(!(config&0x800)){
  std::array<u8,52> bytes{};AnmView info{bytes.data()};info.put(0,52);info.put(4,255);if(!h.pad_winmm_state(bytes,status))return false;if(status)return true;u32 out=held;const u32 buttons=info.get(0x20);
  for(u32 i=0;i<4;++i){i32 index;if(!binding(addresses[i],index))return false;if(index>=0&&(buttons&(1u<<(u32(index)&31))))out|=masks[i];}
  u32 xmin,xmax,ymin,ymax;if(!read(0x540ae8,xmax)||!read(0x540ae4,xmin)||!read(0x540af0,ymax)||!read(0x540aec,ymin))return false;
  const u32 xcenter=(xmin+xmax)>>1,xquarter=(xmax-xmin)>>2,ycenter=(ymin+ymax)>>1,yquarter=(ymax-ymin)>>2;
  if(xcenter+xquarter<info.get(8))out|=0x80;if(info.get(8)<xcenter-xquarter)out|=0x40;if(ycenter+yquarter<info.get(12))out|=0x20;if(info.get(12)<ycenter-yquarter)out|=0x10;result=out;return true;
 }
 u32 device;if(!read(0x4e47f4,device)||!h.pad_direct_poll(device,status))return false;
 if(signed_word(status)<0){if(!read(0x4e47f4,device)||!h.pad_direct_acquire(device,status))return false;if(status==0x8007001e)for(u32 i=0;i<400;++i){if(!read(0x4e47f4,device)||!h.pad_direct_acquire(device,status))return false;if(status!=0x8007001e)break;}return true;}
 std::array<u8,272> bytes{};if(!read(0x4e47f4,device)||!h.pad_direct_state(device,bytes,status))return false;if(signed_word(status)<0)return true;AnmView state{bytes.data()};u32 out=held;
 for(u32 i=0;i<4;++i){i32 index;if(!binding(addresses[i],index))return false;if(index>=128)return false;if(index>=0&&(bytes[48+index]&0x80))out|=masks[i];}
 i32 x,y;if(!binding(0x4e49bc,x)||!binding(0x4e49be,y))return false;const i32 actual_x=signed_word(state.get(0)),actual_y=signed_word(state.get(4));if(actual_x < -x)out|=0x40;if(actual_y < -y)out|=0x10;if(actual_x > x)out|=0x80;if(actual_y > y)out|=0x20;result=out;return true;
}
}
