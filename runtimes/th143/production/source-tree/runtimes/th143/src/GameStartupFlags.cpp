#include "GameStartupFlags.hpp"
namespace th143 {
bool set_application_scene_flags(AnmView game,u32 enabled,u32& result){
    if(!game.data)return false;u32 current=game.get(0xc0);current^=((enabled<<11)^current)&0x800;
    result=((current>>1)^current)&0x400;current^=result;game.put(0xc0,current);return true;
}
}
