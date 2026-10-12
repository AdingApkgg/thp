#include "th14-stage-fade-lifecycle-fixture.cpp"
API(control_tick) u32 control_tick(u32 flags){reset_draw();if(!(flags&0x30))fades.update(false,(flags&5)!=0);fades.draw(renderer,10);renderer.flush();return fades.effects.size();}
