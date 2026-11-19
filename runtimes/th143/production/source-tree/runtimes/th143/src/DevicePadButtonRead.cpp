#include "DevicePadButtonRead.hpp"
namespace th143 {
bool read_device_pad_buttons(std::array<u8,128>& buttons,u32 config,u32 device,DevicePadButtonReadHost& h){
 buttons.fill(0);u32 status;
 if(!(config&0x800)){std::array<u8,52> info{};AnmView{info.data()}.put(0,52);AnmView{info.data()}.put(4,255);if(!h.pad_winmm_state(info,status))return false;if(!status){const u32 mask=AnmView{info.data()}.get(0x20);for(u32 i=0;i<32;++i)if(mask&(1u<<i))buttons[i]=0x80;}return true;}
 if(!h.pad_direct_poll(device,status))return false;
 if(signed_word(status)<0){if(!h.pad_direct_acquire(device,status))return false;if(status==0x8007001e)for(u32 i=0;i<400;++i){if(!h.pad_direct_acquire(device,status))return false;if(status!=0x8007001e)break;}return true;}
 std::array<u8,272> state{};if(!h.pad_direct_state(device,state,status))return false;std::memcpy(buttons.data(),state.data()+48,buttons.size());return true;
}
}
