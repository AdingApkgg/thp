#pragma once
#include "PlayerState.hpp"
#include "AnmState.hpp"
namespace th143 {
struct PlayerDrawHost {
    virtual ~PlayerDrawHost()=default;
    virtual bool draw_player_visual(u32 token,AnmView)=0; //47db40
};
//44e3f0: publish live player position to its embedded VM and configure its
// render flags. The caller supplies the actual renderer for the submission.
bool draw_player(PlayerState&,u32 self,PlayerDrawHost&);
}
