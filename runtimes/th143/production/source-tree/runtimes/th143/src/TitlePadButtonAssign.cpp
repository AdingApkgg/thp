#include "TitlePadButtonAssign.hpp"
namespace th143 {
bool assign_title_pad_button(AnmView t,u32 self,u32 slot,i32 button,TitleOptionControlHost& h){
 if(!t.data||slot>=6)return false;auto get=[&](u32 i){u16 v;std::memcpy(&v,t.data+0x5b38+i*2,2);return v;};auto signed_short=[](u16 v){return v&0x8000?i32(v)-65536:i32(v);};auto put=[&](u32 i,u16 v){std::memcpy(t.data+0x5b38+i*2,&v,2);};
 const u16 previous=get(slot);if(signed_short(previous)==button)return true;
 for(u32 i=0;i<6;++i)if(i!=slot&&signed_short(get(i))==button)put(i,get(slot));put(slot,u16(button));u32 result;return h.title_option_call(0x461870,self,{},result)&&h.title_option_call(0x472be0,0,{7},result);
}
}
