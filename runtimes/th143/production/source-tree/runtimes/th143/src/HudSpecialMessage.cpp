#include "HudSpecialMessage.hpp"
#include "MusicCommandQueue.hpp"
#include <string>
namespace th143 {
namespace {
bool read_word(HudSpecialMessageHost& h,u32 p,u32& value){return h.special_message_read(p,&value,4);}
bool string(HudSpecialMessageHost& h,u32 p,std::string& out,u32 limit){out.clear();for(u32 i=0;i<limit;++i){u8 v;if(!h.special_message_read(p+i,&v,1))return false;if(!v)return true;out+=char(v);}return false;}
}
bool create_hud_special_message(AnmView root,u32 flags,i32 id,HudSpecialMessageHost& h){
 if(id!=-1&&id!=-2&&id!=-3)return false;if(!(flags&0x400))return true;root.put(0x80,root.get(0x80)|0x10);
 if(id==-2){u32 special;u8 state;if(!read_word(h,0x4e6a0c,special)||!h.special_message_read(special+0x7c,&state,1))return false;
  if(state&0x80)return h.special_message_game_over(0);u32 token;return read_word(h,0x4e6a5c,token)&&h.special_message_statistics_begin(token);
 }
 u32 live_flags,descriptor;if(!read_word(h,0x4e47b0,live_flags)||!read_word(h,0x4e6bac,descriptor))return false;
 if((live_flags&0x60)==0x40){u32 root_token,mode;if(!read_word(h,0x4e6a5c,root_token)||!read_word(h,root_token+0x94,mode))return false;
  if(!mode){u32 name;std::string requested,current;if(!read_word(h,descriptor+0xc,name)||!string(h,name,requested,252)||!string(h,0x53d5d8,current,256))return false;
   requested+=".wav";if(requested==current)return true;
  }
 }
 u8 config;u32 track;if(!h.special_message_read(0x4e49dc,&config,1)||!read_word(h,descriptor+0x18,track))return false;
 auto audio=h.special_message_audio();if(!audio.data)return false;MusicCommandQueue queue;std::memcpy(queue.data.data(),audio.data+0x24f8,queue.data.size());
 if((config&0x10)&&!queue.enqueue(4,0,"dummy"))return false;if(!queue.enqueue(2,id==-1?1:0,"dummy"))return false;
 std::memcpy(audio.data+0x24f8,queue.data.data(),queue.data.size());
 u32 save;if(!read_word(h,0x4e6b9c,save))return false;const u8 unlocked=1;return h.special_message_write(save+track+0xef74,&unlocked,1);
}
}
