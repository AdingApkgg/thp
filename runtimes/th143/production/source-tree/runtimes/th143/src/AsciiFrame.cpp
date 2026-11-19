#include "AsciiFrame.hpp"
namespace th143 {
bool age_ascii_entries(AnmView owner){
    if(!owner.data)return false;const i32 count=signed_word(owner.get(0x191ac));if(count>320)return false;u32 kept=0;
    for(i32 i=0;i<count;++i){auto entry=owner.sub(0xbac+u32(i)*0x138);const u32 lifetime=entry.get(0x12c)-1;entry.put(0x12c,lifetime);if(signed_word(lifetime)<0)continue;
        if(kept!=u32(i))std::memmove(owner.data+0xbac+kept*0x138,entry.data,0x138);++kept;
    }
    owner.put(0x191ac,kept);return true;
}
bool advance_ascii_frame(AnmView owner){if(!age_ascii_entries(owner))return false;owner.put(0x191e0,owner.get(0x191e0)+1);return true;}
}
