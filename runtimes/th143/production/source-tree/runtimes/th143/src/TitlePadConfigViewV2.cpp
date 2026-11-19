#include "TitlePadConfigViewV2.hpp"
namespace th143 {
bool refresh_title_pad_config_view_v2(AnmView title,u32 self,TitleOptionViewHost& h){
 if(!title.data)return false;for(u32 row=0;row<4;++row)for(u32 selected=0;selected<2;++selected)for(u32 digit=0;digit<2;++digit){
  const i32 script=53+i32(row*2+selected*8+digit);u32 vm;if(!h.title_option_child(self,2,script,vm))return false;if(!vm)continue;u16 raw;std::memcpy(&raw,title.data+0x5b38+row*2,2);const i32 value=raw&0x8000?i32(raw)-65536:i32(raw),n=digit?value%10:value/10;u32 resource,result;if(!h.title_option_read(vm+0x30,&resource,4)||!h.title_option_call(0x473a00,resource,{vm,u32(36+n)},result))return false;
 }return true;
}
}
