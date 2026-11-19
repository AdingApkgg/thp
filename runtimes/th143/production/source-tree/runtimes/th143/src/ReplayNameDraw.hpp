#pragma once
#include "AnmState.hpp"
#include <array>
#include <vector>
namespace th143 {
struct ReplayNameDrawHost {
 virtual ~ReplayNameDrawHost()=default;
 virtual bool replay_name_draw_read(u32,void*,u32)=0;
 virtual bool replay_name_draw_write(u32,const void*,u32)=0;
 virtual bool replay_name_ascii(u32 ascii,std::array<u32,3>& position,u32 format,const std::vector<u32>&)=0;
};
// Full447ed0; the three incoming position words are passed by value. Name,
// caret and91 character/icon cells use the caller's existing font/shadow.
bool draw_replay_name(AnmView menu,u32 self,std::array<u32,3> position,ReplayNameDrawHost&);
}
