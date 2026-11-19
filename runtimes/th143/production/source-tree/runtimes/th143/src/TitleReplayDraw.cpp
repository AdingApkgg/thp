#include "TitleReplayDraw.hpp"
namespace th143 {
bool draw_title_replay(AnmView t,TitleReplayDrawHost& h,u32& result){
 if(!t.data)return false;result=1;if(t.get(0x24)!=2)return true;auto read=[&](u32 p,u32& v){return h.title_replay_draw_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.title_replay_draw_write(p,&v,4);};u32 ascii,start_y,step_y;if(!read(0x4e69f8,ascii)||!read(0x4c9edc,start_y)||!read(0x4c9e88,step_y)||!write(ascii+0x191c4,1))return false;
 float y=real(start_y);std::array<u32,3> position{0x42e40000,start_y,0};const u32 first=t.get(0x1d8)*25;u32 slot=0x5b54+first*4;
 for(u32 i=first;signed_word(i)<signed_word((t.get(0x1d8)+1)*25);++i,slot+=4){if(!write(ascii+0x191b0,t.get(0x28)==u32(signed_word(i)%25)?0xffffff00:0xff808080))return false;const u32 object=t.get(slot);u32 format;
  if(object){u32 header;if(!read(object+0x1c,header))return false;std::array<i32,9> tm;if(!h.title_replay_localtime(header+0x14,tm))return false;u32 first_arg;
   if(!t.get(0x1d8)){first_arg=i+1;if(!read(0x4c7ec0,format))return false;}
   else{u32 tag;if(!read(t.get(slot)+0x83,tag)||!write(0x541154,tag))return false;const u8 zero=0;if(!h.title_replay_draw_write(0x541158,&zero,1)||!read(0x4c7ec8,format))return false;first_arg=0x541154;}
   u32 percent,day,scene;if(!read(header+0x7c,percent)||!read(header+0x88,day)||!read(header+0x8c,scene))return false;const double value=double(real(percent));std::uint64_t encoded;std::memcpy(&encoded,&value,8);
   const std::vector<u32> args{first_arg,header,u32(tm[5]%100),u32(tm[4])+1,u32(tm[3]),u32(tm[2]),u32(tm[1]),day+1,scene+1,u32(encoded),u32(encoded>>32)};u32 current;if(!read(0x4e69f8,current)||!h.title_replay_ascii(current,position,format,args))return false;
  }else{if(!read(0x4c7ec0+(!t.get(0x1d8)?1:3)*4,format)||!h.title_replay_ascii(ascii,position,format,{i+1}))return false;}
  y+=real(step_y);position[1]=word(y);if(!read(0x4e69f8,ascii))return false;
 }
 return write(ascii+0x191b0,0xffffffff)&&write(ascii+0x191c4,0);
}
}
