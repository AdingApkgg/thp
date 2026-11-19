#include "MusicRoomComments.hpp"
namespace th143 {
bool parse_music_room_comments(AnmView title,u32 declared,std::vector<u8>& backing,u32& records){
 if(!title.data||declared>backing.size())return false;u32 remaining=declared,at=0;records=0;
 while(signed_word(remaining)>0){
  if(at>=backing.size())return false;
  if(backing[at]=='@'){
   if(records>=32)return false;++at;
   auto line=[&](u32 offset,u32 capacity){u32 next;if(!copy_music_comment_line(backing.data(),backing.size(),at,remaining,title.data+offset,capacity,next))return false;at=next;return true;};
   if(!line(0x804+records*0x40,0x40)||!line(0x1004+records*0x42,0x42))return false;
   for(u32 i=0;i<8;++i)if(!line(0x1844+(records*8+i)*0x42,0x42))return false;++records;
  }else{u32 next;if(!skip_music_comment_line(backing.data(),backing.size(),at,remaining,next))return false;at=next;}
 }
 return true;
}
}
