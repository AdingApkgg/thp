#pragma once
#include "TitleMusicControl.hpp"
#include <vector>
namespace th143 {
struct TitleMusicEntryHost:TitleMusicControlHost {
 // File allocation padding is supplied explicitly, as for titlemsg.txt.
 virtual bool title_music_file(u32 name,u32& token,u32& declared,std::vector<u8>& backing)=0;
};
// Complete466650 phase0 through45f6e0, positive entry clock domain.
bool advance_title_music_entry(AnmView title,u32 self,TitleMusicEntryHost&,u32& result);
}
