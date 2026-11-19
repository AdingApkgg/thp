#include "HudMessageFlow.hpp"
#include <array>
namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void set_timer(AnmView s,u32 at,u32 value,HudMessageFlowHost& h){if(!(s.get(at+16)&1)){s.put(at+12,h.global_rate_token());s.put(at+16,s.get(at+16)|1);}s.put(at,value-1);s.put(at+4,value);s.put(at+8,word(float(signed_word(value))));}
bool tick_timer(AnmView s,u32 at,bool down,HudMessageFlowHost& h){
 const u32 pointer=s.get(at+12),old=s.get(at+4);float rate=1;if(pointer&&!h.timer_rate(pointer,rate))return false;const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
 const float delta=unit?1.f:rate,value=down?s.floating(at+8)-delta:s.floating(at+8)+delta;s.put(at,old);s.put(at+4,unit?(down?old-1:old+1):truncate(value));s.put(at+8,word(value));return true;
}
u32 repeat_count(const HudMessageInput& input,u32 index){return input.held&(1u<<index)?(index==9?input.skip_counter:input.confirm_counter):0;}
}
bool step_hud_message_flow(AnmView s,const HudMessageInput& input,HudMessageFlowHost& host,i32& result,u32 budget){
 result=0;if(signed_word(s.get(0x180))>0)s.put(0x180,s.get(0x180)-1);if(input.fresh&0x201)s.put(0x184,s.get(0x184)|0x40);
 if((s.get(0x184)&0x41)==0x41&&(((input.held&0x200)&&input.skip_counter>=20)||((input.held&1)&&input.confirm_counter>=20))){u16 time;if(!host.message_read(s.get(0x158),&time,2))return false;set_timer(s,0x18,time,host);}
 bool waiting=false;
 for(u32 count=0;;++count){
  if(count>=budget)return false;const u32 pc=s.get(0x158);std::array<u8,4> header;if(!host.message_read(pc,header.data(),4))return false;u16 time;std::memcpy(&time,header.data(),2);
  if(signed_word(s.get(0x1c))<time)break;
  const u8 op=header[2],n=header[3];std::array<u8,255> payload;if(n&&!host.message_read(pc+4,payload.data(),n))return false;
  if(op==0){result=-1;return true;}
  if(op==11){
   if(n<4)return false;u32 duration;std::memcpy(&duration,payload.data(),4);if(signed_word(s.get(0x30))<=0)set_timer(s,0x2c,duration,host);if(!tick_timer(s,0x2c,true,host))return false;
   const bool confirm=(input.fresh&0x80001)||signed_word(s.get(0x30))<=0;
   const bool skip=!confirm&&(s.get(0x184)&0x41)==0x41&&(repeat_count(input,9)>=20||repeat_count(input,0)>=20);
   if(!confirm&&!skip){waiting=true;break;}
   if(confirm&&!host.message_play_sound(0))return false;set_timer(s,0x2c,0,host);s.put(0x188,0);s.put(0x18c,0);
  }else if(op==10||op==12||op==13||op==14||op==28||op==29){if(!execute_hud_message_control(s,op,payload.data(),n,host))return false;}
  else if(op==26)s.put(0x184,s.get(0x184)|2);
  else if(op!=3&&op!=30&&op<34){if(!host.message_external_instruction(s,op,payload.data(),n))return false;}
  // Immediate ANM callbacks can change the instruction pointer; reread it.
  std::array<u8,4> current;if(!host.message_read(s.get(0x158),current.data(),4))return false;s.put(0x158,s.get(0x158)+4+current[3]);
 }
 if(!waiting&&!tick_timer(s,0x18,false,host))return false;
 auto indicator=host.message_visual(s.get(0x6c));if(!indicator.data){s.put(0x6c,0);result=0;return true;}return host.message_indicator(s,indicator,result);
}
}
