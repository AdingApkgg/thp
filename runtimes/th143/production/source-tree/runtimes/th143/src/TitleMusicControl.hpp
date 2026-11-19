#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct TitleMusicControlHost:AnmTimerHost {
 virtual bool title_music_read(u32,void*,u32)=0;
 virtual bool title_music_write(u32,const void*,u32)=0;
 //418300 carries copied target xyz;444660 omits its unused first argument.
 virtual bool title_music_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
//45f6e0 state6 ->466650 phases1..3 plus outer Title clock. Entry phase0
// resource/text/animation creation is supplied by a separate implementation.
bool advance_title_music_control(AnmView title,u32 self,TitleMusicControlHost&,u32& result);
}
