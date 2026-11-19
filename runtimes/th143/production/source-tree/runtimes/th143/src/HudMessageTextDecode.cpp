#include "HudMessageTextDecode.hpp"
namespace th143 {
bool decode_hud_message_text(const u8* encoded,u32 available,u8* output,u32 capacity,u32& written){
 written=0;if(!encoded||!output)return false;u8 key=0x77,step=7;
 for(u32 i=0;i<available&&i<capacity;++i){const u8 value=encoded[i]^key;key=u8(key+step);step=u8(step+0x10);output[i]=value;++written;if(!value)return true;}return false;
}
}
