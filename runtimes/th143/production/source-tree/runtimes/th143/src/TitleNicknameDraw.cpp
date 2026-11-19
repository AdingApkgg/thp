#include "TitleNicknameDraw.hpp"
namespace th143 {
bool draw_title_nickname(AnmView t,TitleNicknameDrawHost& h,u32& result){
 if(!t.data)return false;result=1;if(t.get(0x24)!=1)return true;auto read=[&](u32 p,u32& value){return h.nickname_draw_read(p,&value,4);};auto write=[&](u32 p,u32 value){return h.nickname_draw_write(p,&value,4);};u32 notice;if(!read(0x4e6b80,notice))return false;if(notice)return true;
 u32 start_x,start_y,step_x,step_y,ascii;if(!read(0x4c9ef4,start_x)||!read(0x4c9ed8,start_y)||!read(0x4c9eb4,step_x)||!read(0x4c9eac,step_y)||!read(0x4e69f8,ascii)||!write(ascii+0x191c8,4)||!write(ascii+0x191c4,1))return false;
 float x=real(start_x),y=real(start_y);std::array<u32,3> position{start_x,start_y,0};
 for(u32 i=0;i<70;++i){if(!write(ascii+0x191b0,t.get(0x28)==i?0xffffffff:0xff707070))return false;u32 save;u8 unlocked;if(!read(0x4e6b9c,save)||!h.nickname_draw_read(save+0xeff9+i,&unlocked,1))return false;
  if(unlocked||i<60){if(!h.nickname_ascii(ascii,position,unlocked?0x4c7d24:0x4c7d28,i+1)||!read(0x4e69f8,ascii))return false;}
  if(i%10==9){y+=real(step_y);x=real(start_x);position[1]=word(y);}else x+=real(step_x);position[0]=word(x);
 }
 return write(ascii+0x191c8,0)&&write(ascii+0x191c4,0);
}
}
