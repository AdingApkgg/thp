#include "HudClearBonus.hpp"
namespace th143 {
void award_hud_clear_bonus(AnmView hud,u32& score,u32 rate){
 hud.put(0x2b0,100000);score+=10000;if(score>=1000000000)score=999999999;
 hud.put(0x180,hud.get(0x180)|0x100u);
 if(!(hud.get(0x194)&1)){hud.put(0x190,rate);hud.put(0x194,hud.get(0x194)|1u);}
 hud.put(0x184,0xffffffff);hud.put(0x188,0);hud.put(0x18c,0);
}
}
