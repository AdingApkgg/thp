#include "PlayerAlternate.hpp"
namespace th143 {
bool release_player_alternate(PlayerAlternateGlobals& g,AnmWorld& world,PlayerAlternateHost& host){
    if(g.secondary!=5)return true;
    if(!g.player||!host.alternate_bullet_circle(g.player+0x5e0,48.f,0))return false;
    const u32 position=g.player+0x5e0,manager=g.lasers;
    std::array<u32,3> coordinates;u32 beam;
    if(!g.player||!manager||!host.alternate_read(position,coordinates.data(),12)||!host.alternate_read(manager+0x18,&beam,4)||!host.alternate_write(manager+0x5dc,coordinates.data(),12))return false;
    u32 budget=100000;
    while(beam){
        if(!budget--)return false;u32 mode,next;
        if(!host.alternate_read(beam+0x10,&mode,4)||!host.alternate_read(beam+8,&next,4))return false;
        if(mode!=1&&!host.alternate_beam_circle(beam,position,48.f,0,false))return false;
        beam=next;
    }
    AnmView cheat{nullptr};if(!g.cheat||!host.alternate_cheat_view(g.cheat,cheat)||!cheat.data)return false;
    return signal_cheat_child(cheat,cheat.get(0x2b8),12,6,world)&&signal_cheat_child(cheat,cheat.get(0x2b8),8,6,world);
}
}
