#include "MusicCommentLine.hpp"
namespace th143 {
namespace {bool newline(u8 c){return c==10||c==13;}}
bool skip_music_comment_line(const u8* source,u32 capacity,u32 offset,u32& remaining,u32& next){
 if(!source||offset>=capacity||remaining>=capacity-offset)return false;u32 p=offset;
 while(!newline(source[p])){if(!remaining){next=p;return true;}++p;--remaining;}
 if(remaining)while(newline(source[p])){if(!remaining)break;++p;--remaining;}
 next=p;return true;
}
bool copy_music_comment_line(u8* source,u32 capacity,u32 offset,u32& remaining,u8* destination,u32 destination_bytes,u32& next){
 if(!source||offset>=capacity||remaining>=capacity-offset)return false;u32 p=offset;
 while(!newline(source[p])){if(!remaining){next=p;return true;}++p;--remaining;}
 if(remaining){
  u32 n=0;while(offset+n<p&&source[offset+n])++n;
  if(!destination||n>=destination_bytes)return false;source[p]=0;std::memcpy(destination,source+offset,n);destination[n]=0;++p;--remaining;
  while(newline(source[p])){if(!remaining)break;++p;--remaining;}
 }
 next=p;return true;
}
}
