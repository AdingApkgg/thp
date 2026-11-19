#include "HudMessageControl.hpp"
namespace th143 {
bool execute_hud_message_control(AnmView s,u8 op,const u8* p,u32 n,HudMessageControlHost& host){
 auto get=[&](u32 at){u32 v;std::memcpy(&v,p+at,4);return v;};
 if(op==12){s.put(0x180,1);return true;}
 if(!p||n<4)return false;const u32 first=get(0);
 switch(op){
 case 10:s.put(0x184,(s.get(0x184)&~1u)|(first&1));return true;
 case 13:return host.message_signal_immediate(s.get(0x40),signed_word(first+17));
 case 14:{if(n<8)return false;const u32 index=get(4);if(index>=5)return false;return host.message_signal_immediate(s.get(0x44+index*4),signed_word(first+17));}
 case 28:if(n<8)return false;s.put(0x1a0,word(real(first)*2.f));s.put(0x1a4,word(real(get(4))*2.f));return true;
 case 29:s.put(0x184,(s.get(0x184)&~0x3cu)|((first<<2)&0x3c));return true;
 default:return false;
 }
}
}
