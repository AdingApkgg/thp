#pragma once
#include "AnmState.hpp"
namespace th143 {
struct TitleQuitControlHost:AnmTimerHost {
 virtual bool title_quit_read(u32,u32&)=0;
 virtual bool title_quit_write(u32,u32)=0;
 virtual bool title_quit_queue(u32 owner,u32 kind,u32 value,u32 name)=0;
};
//45f6e0 states2/8/10, full4447e0 music stop, and the outer Title clock.
//Application transition, destruction and the eventual WinMain file write follow
//outside the scheduler callback; they are deliberately not performed here.
bool advance_title_quit_control(AnmView,TitleQuitControlHost&,u32& result);
}
