#pragma once
#include "AnmState.hpp"
#include <array>
#include <vector>
namespace th143 {
struct TitleReplayDrawHost {
 virtual ~TitleReplayDrawHost()=default;
 virtual bool title_replay_draw_read(u32,void*,u32)=0;
 virtual bool title_replay_draw_write(u32,const void*,u32)=0;
 virtual bool title_replay_localtime(u32 time_address,std::array<i32,9>&)=0;
 virtual bool title_replay_ascii(u32 ascii,std::array<u32,3>& position,u32 format,const std::vector<u32>& arguments)=0;
};
// Full465690. CRT localtime and variadic ASCII queue are explicit services.
bool draw_title_replay(AnmView title,TitleReplayDrawHost&,u32& result);
}
