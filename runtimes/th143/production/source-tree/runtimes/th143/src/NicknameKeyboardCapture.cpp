#include "NicknameKeyboardCapture.hpp"
namespace th143 {
bool capture_nickname_keyboard(std::array<u8,256>& out,bool enabled,u32 config,DeviceInputHost& h,u32& mode){out.fill(0);mode=0;if(!enabled)return true;u32 status;const bool direct=(config&0x400)!=0;if(!h.keyboard_state(direct,out,status))return false;if(direct){if(status&&!h.acquire_keyboard(status))return false;mode=1;}else mode=2;return true;}
}
