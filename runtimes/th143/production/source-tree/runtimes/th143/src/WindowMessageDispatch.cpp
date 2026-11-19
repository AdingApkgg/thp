#include "WindowMessageDispatch.hpp"
namespace th143 {
bool dispatch_window_message(u32 window,u32 message,u32 wparam,u32 lparam,WindowMessageDispatchHost& h,u32& result){
 auto read=[&](u32 p,u32& v){return h.window_message_read(p,v);};auto write=[&](u32 p,u32 v){return h.window_message_write(p,v);};
 auto call=[&](u32 slot,std::initializer_list<u32> args){return h.window_message_call(slot,args,result);};
 auto fallback=[&](){return call(0x4b8258,{window,message,wparam,lparam});};
 if(message==0x14){result=1;return true;}
 if(message==0x1c){if(!write(0x5390b0,wparam)||!write(0x5390b4,wparam==0))return false;return fallback();}
 if(message==5){u32 flags;if(!read(0x53b0dc,flags))return false;if((flags&1)&&wparam==2){flags|=2;if(!write(0x53b0dc,flags))return false;const u32 mode=(flags>>2)&15;if(mode==3)flags&=0xffffffc3;else if(mode==4)flags=(flags&0xffffffc7)|4;else if(mode==5)flags=(flags&0xffffffcb)|8;else return fallback();if(!write(0x53b0dc,flags))return false;}return fallback();}
 if(message==0x10){u32 flags;if(!read(0x4e4ef4,flags)||!write(0x4e4ef4,(flags&0xfffffeff)|0x80))return false;result=1;return true;}
 if(message==0x20){u32 windowed;if(!read(0x4e48e4,windowed))return false;
  if(windowed){if(!call(0x4b8274,{0,0x7f00}))return false;const u32 cursor=result;if(!call(0x4b8228,{cursor})||!call(0x4b8240,{1}))return false;}
  else{u32 inactive;if(!read(0x5390b4,inactive))return false;if(inactive){if(!call(0x4b8274,{0,0x7f00}))return false;const u32 cursor=result;if(!call(0x4b8228,{cursor}))return false;do{if(!call(0x4b8240,{1}))return false;}while(signed_word(result)<0);}
   else{do{if(!call(0x4b8240,{0}))return false;}while(signed_word(result)>=0);if(!call(0x4b8228,{0}))return false;}}
  result=1;return true;
 }
 if(message==0x104&&wparam==13){u32 flags;if(!read(0x53b0dc,flags))return false;flags|=2;if(!write(0x53b0dc,flags))return false;const u32 mode=(flags>>2)&15;if(mode<=5){const u32 next=(mode+3)%6;flags=(flags&(0xffffffc3|(next<<2)))|(next<<2);if(!write(0x53b0dc,flags))return false;}return fallback();}
 if(message==0x112){const u32 command=wparam&0xfff0;if(command==0xf090||command==0xf100){result=1;return true;}}
 if(message==0x201){if(!call(0x4b8230,{window}))return false;return fallback();}
 return fallback();
}
}
