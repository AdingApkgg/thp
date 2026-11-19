#include "TitleOptionView.hpp"
namespace th143 {
namespace {i32 signed_byte(u8 v){return v&0x80?i32(v)-256:i32(v);}u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}}
bool refresh_title_option_view(AnmView title,u32 self,TitleOptionViewHost& h){
 if(!title.data)return false;auto byte=[&](u32 p,i32& out){u8 v;if(!h.title_option_read(p,&v,1))return false;out=signed_byte(v);return true;};auto write=[&](u32 p,u32 v){return h.title_option_write(p,&v,4);};u32 result;i32 first,second;
 if(!byte(0x4e49c6,first)||!write(0x540984,u32(first))||!h.title_option_call(0x4737b0,0x53b1e0,{8,0,0x4c7ef8},result)||!byte(0x4e49c7,second)||!write(0x540988,u32(second)))return false;
 u32 level=0xffffd8f0;if(second){const float fraction=float(first)/100.f;float inverse=1.f-fraction;inverse*=inverse;inverse*=inverse;float value=1.f-inverse;value*=-5000.f;level=0xffffec78-truncate(value);}if(!write(0x54098c,level))return false;
 constexpr i32 scripts[4][3]={{25,26,27},{29,30,31},{33,34,35},{37,38,39}};
 for(u32 group=0;group<4;++group)for(u32 digit=0;digit<3;++digit){
  u32 vm;if(!h.title_option_child(self,1,scripts[group][digit],vm))return false;if(!vm)continue;i32 value;if(!byte(group<2?0x4e49c6:0x4e49c7,value))return false;const i32 n=digit==0?value/100:digit==1?(value/10)%10:value%10;u32 resource;if(!h.title_option_read(vm+0x30,&resource,4)||!h.title_option_call(0x473a00,resource,{vm,u32((group%2?47:36)+n)},result))return false;
 }
 auto visibility=[&](u32 p,const std::array<i32,4>& children){i32 value;if(!byte(p,value))return false;for(u32 i=0;i<4;++i){u32 vm,flags;if(!h.title_option_child(self,1,children[i],vm)||!vm||!h.title_option_read(vm+0x18,&flags,4))return false;const bool shown=value>=100||(value>=10&&(i%2));if(!write(vm+0x18,shown?flags|2:flags&~2u))return false;}return true;};
 return visibility(0x4e49c6,{25,26,29,30})&&visibility(0x4e49c7,{33,34,37,38});
}
}
