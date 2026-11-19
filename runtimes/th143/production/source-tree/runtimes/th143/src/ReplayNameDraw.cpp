#include "ReplayNameDraw.hpp"
namespace th143 {
bool draw_replay_name(AnmView m,u32 self,std::array<u32,3> position,ReplayNameDrawHost& h){
 if(!m.data)return false;auto read=[&](u32 p,u32& v){return h.replay_name_draw_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.replay_name_draw_write(p,&v,4);};u32 ascii;if(!read(0x4e69f8,ascii)||!h.replay_name_ascii(ascii,position,0x4c6794,{self+0x2cc}))return false;const u32 length=m.get(0x1f0);float x=real(position[0])+float(signed_word(length*9));if(length==12){u32 back;if(!read(0x4c9e74,back))return false;x-=real(back);}position[0]=word(x);if(!read(0x4e69f8,ascii)||!write(ascii+0x191b0,0xffffff00)||!h.replay_name_ascii(ascii,position,0x4c6798,{}))return false;
 u32 start_x,start_y,step_x,step_y;if(!read(0x4c9f1c,start_x)||!read(0x4c9f3c,start_y)||!read(0x4c9e90,step_x)||!read(0x4c9e8c,step_y)||!read(0x4e69f8,ascii)||!write(ascii+0x191b0,0xffffffff))return false;float gx=real(start_x),gy=real(start_y);std::array<u32,3> grid{start_x,start_y,0};
 for(u32 i=0;i<91;++i){if(!write(ascii+0x191b0,m.get(0x110)==i?0xffffff00:0xff808080))return false;u32 character;if(i<88){u8 c;if(!h.replay_name_draw_read(0x4c65f0+i,&c,1))return false;character=c&0x80?u32(i32(c)-256):c;}else character=i==88?0x81:i==89?0x7f:0x80;if(!h.replay_name_ascii(ascii,grid,0x4c679c,{character}))return false;if(i%13==12){gx=real(start_x);gy+=real(step_y);grid[1]=word(gy);}else gx+=real(step_x);grid[0]=word(gx);if(i<90&&!read(0x4e69f8,ascii))return false;}
 return read(0x4e69f8,ascii)&&write(ascii+0x191b0,0xffffffff);
}
}
