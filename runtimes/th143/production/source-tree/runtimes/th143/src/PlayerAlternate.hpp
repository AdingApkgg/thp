#pragma once
#include "CheatAnimation.hpp"
namespace th143 {
struct PlayerAlternateGlobals {u32 secondary=0,player=0,lasers=0,cheat=0;};
struct PlayerAlternateHost {
    virtual ~PlayerAlternateHost()=default;
    virtual bool alternate_read(u32,void*,u32)=0;
    virtual bool alternate_write(u32,const void*,u32)=0;
    virtual bool alternate_cheat_view(u32 token,AnmView&)=0;
    // Position remains a live guest address for callbacks that can move the
    // player; circle is417540 and beam is its virtual table+24 method.
    virtual bool alternate_bullet_circle(u32 position,float radius,i32 kind)=0;
    virtual bool alternate_beam_circle(u32 beam,u32 position,float radius,i32 kind,bool items)=0;
};
//4508e0. Only secondary5 runs the radius48 cancellation. Every beam's next
//is cached before its callback; player/global owners are reread after bullets.
bool release_player_alternate(PlayerAlternateGlobals&,AnmWorld&,PlayerAlternateHost&);
}
