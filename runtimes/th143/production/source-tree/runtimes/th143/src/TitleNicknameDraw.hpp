#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct TitleNicknameDrawHost {
 virtual ~TitleNicknameDrawHost()=default;
 virtual bool nickname_draw_read(u32,void*,u32)=0;
 virtual bool nickname_draw_write(u32,const void*,u32)=0;
 virtual bool nickname_ascii(u32 ascii,std::array<u32,3>& position,u32 format,u32 value)=0;
};
//Full466340: 70 numbered cells, locked lastrow hidden, selected color and
//ASCII font/alignment state. Active only phase1 without a Notice owner.
bool draw_title_nickname(AnmView title,TitleNicknameDrawHost&,u32& result);
}
