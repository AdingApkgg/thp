#include "HudScene.hpp"

namespace th143 {
bool begin_hud_scene(AnmView hud,HudSceneHost& host){
    if(!host.hud_scene_signal(hud.get(0x110),1)||!host.hud_scene_signal(hud.get(0x114),1))return false;
    hud.put(0x180,hud.get(0x180)&~0x100u);
    const u32 flags=hud.get(0x194);
    if(!(flags&1)){hud.put(0x190,0x4e40b0);hud.put(0x194,flags|1);}
    hud.put(0x188,0);hud.put(0x18c,0);hud.put(0x184,0xffffffff);return true;
}
}
