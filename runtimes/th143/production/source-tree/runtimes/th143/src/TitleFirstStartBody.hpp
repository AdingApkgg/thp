#pragma once
#include "AnmState.hpp"
namespace th143 {
struct TitleFirstStartBindings {AnmView title,application,game;u32& scene_descriptor;};
struct TitleFirstStartHost {
    virtual ~TitleFirstStartHost()=default;
    virtual bool first_start_transition(u32& handle)=0;
    virtual bool first_start_signal(u32 handle,i32 id)=0;
    virtual bool first_start_ascii(u32 x_word,u32 y_word)=0;
    virtual bool first_start_title_state(i32)=0;
    virtual bool first_start_clear_title()=0;
    virtual bool first_start_fade(u32 duration_word)=0;
    virtual bool first_start_initialize_game(u32 mode)=0;
    virtual bool first_start_message(u32 id)=0;
};
//45fb70 substate5 body, selected by the actual entry switch. Helpers below
//are explicit boundaries; caller45f6e0 timer tail is separate.
bool advance_title_first_start_body(TitleFirstStartBindings&,TitleFirstStartHost&,u32& result);
}
