#include "HudMessagePortraitControl.hpp"
namespace th143 {
bool execute_hud_message_portrait_control(AnmView s,u8 op,HudMessagePortraitControlHost& h){
 auto signal=[&](u32 at,i32 value,bool immediate=false){return h.portrait_control_signal(s.get(at),value,immediate);};
 auto argument=[&](u32& value){return h.portrait_control_read(s.get(0x158)+4,value);};u32 index;
 switch(op){
 case 4:if(!signal(0x40,1))return false;s.put(0x40,0);return true;
 case 5:if(!argument(index)||index>=5||!signal(0x44+index*4,1)||!argument(index)||index>=5)return false;s.put(0x44+index*4,0);return signal(0x68,1);
 case 6:case 18:
  if(op==18&&!h.portrait_control_discard_indicator(s))return false;
  for(u32 at=0x58;at<=0x64;at+=4)if(!signal(at,op==6?1:3))return false;
  return op==18||h.portrait_control_discard_indicator(s);
 case 23:return signal(0x40,7);
 case 24:return signal(0x44,7)&&signal(0x48,7);
 case 25:
  for(u32 at=0x58;at<=0x64;at+=4){auto v=h.portrait_control_visual(s.get(at));if(!v.data){s.put(at,0);return false;}u32 value;if(!argument(value))return false;v.put(0x4f0,word(float(signed_word(value))));}return true;
 case 7:
  for(u32 at=0x44;at<=0x50;at+=4)if(!signal(at,3,true))return false;
  if(!signal(0x40,2,true)||!signal(0x54,2))return false;s.put(0x190,0);break;
 case 8:
  if(!signal(0x40,3,true)||!argument(index)||index>=5||!signal(0x44+index*4,2,true)||!signal(0x54,3))return false;s.put(0x190,1);break;
 case 32:if(!signal(0x54,3)||!argument(index))return false;s.put(0x190,index);break;
 default:return false;
 }
 for(u32 at=0x58;at<=0x64;at+=4){auto v=h.portrait_control_visual(s.get(at));if(!v.data){s.put(at,0);return false;}v.put(0x4f0,0);}
 s.put(0x184,s.get(0x184)&~2u);s.put(0x188,0);s.put(0x18c,0);return true;
}
}
