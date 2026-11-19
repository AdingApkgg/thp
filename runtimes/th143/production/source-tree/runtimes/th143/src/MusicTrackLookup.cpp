#include "MusicTrackLookup.hpp"
namespace th143 {
bool find_music_track(const u8* table,u32 mapped_bytes,const char* path,u32 path_bytes,u32& track){
    track=0;if(!table||!path)return false;u32 end=0,forward=0,backward=0;
    while(end<path_bytes&&path[end]){if(path[end]=='/')forward=end+1;if(path[end]=='\\')backward=end+1;++end;}
    if(end==path_bytes)return false;
    // The original looks for '/' first and consults '\\' only when no slash
    // exists, including paths containing both separator kinds.
    const u32 base=forward?forward:backward;
    for(u32 index=0,at=0;;++index){
        if(at>=mapped_bytes)return false;if(!table[at])return true;
        u32 n=0;bool equal=false;
        for(;;++n){if(n>=mapped_bytes-at)return false;const u8 a=table[at+n],b=u8(path[base+n]);if(a!=b)break;if(!a){equal=true;break;}if(base+n==end)return false;}
        if(equal){track=index;return true;}
        if(at>0xffffffffu-0x34)return false;at+=0x34;
    }
}
}
