#include "RootFrame.hpp"

namespace th143 {
void root_score_display(AnmView hud,RootFrameGlobals& g){
    if(g.score!=hud.get(0x144)){
        const u32 delta=g.score-hud.get(0x144);u32 speed=delta>>5;
        if(signed_word(speed)>=0x8d55e)speed=0x8d55e;else if(!speed)speed=1;
        if(signed_word(hud.get(0x148))<signed_word(speed))hud.put(0x148,speed);
        if(signed_word(hud.get(0x148))>signed_word(delta))hud.put(0x148,delta);
        hud.put(0x144,hud.get(0x144)+hud.get(0x148));
        if(signed_word(hud.get(0x144))>=signed_word(g.score))hud.put(0x148,0);
    }
    if(signed_word(g.high_score)<signed_word(hud.get(0x144))){g.high_score=hud.get(0x144);g.high_score_scene=g.scene;g.game_flags|=8;}
}
i32 root_frame(RootState& root,AnmView hud,RootFrameGlobals& g,RootFrameHost& host){
    auto r=root.view();u32 flags=r.get(0x80);
    if(flags&0x4000){
        if(flags&0x10)return 3;
        const u32 time=r.get(0x98)+1;r.put(0x98,time);
        if(time==180&&!host.notice(0,200,5))return -2;
        if(signed_word(time)>=380){if(!r.get(0x94))g.application_state=(g.config&0x2000)?2:15;else if(!host.replay_exit())return -2;}
    }
    if((hud.get(0x180)&0x100)&&signed_word(hud.get(0x188))<120&&!(r.get(0x80)&0x10))return 1;
    const u32 time=r.get(0x14);
    if((!time||(time==30&&(r.get(0x80)&0x800)))&&!host.start_or_restart(root,g))return -2;
    const u32 live_time=r.get(0x14);if(live_time==5)g.presentation=2;
    if(g.previous_dialog&&(g.previous_dialog_flags&8)){if(!host.erase_previous_dialog())return -2;g.previous_dialog=false;}
    flags=r.get(0x80);if(flags&4){r.put(0x80,flags|0x80);return 1;}
    if(g.game_flags&0x80){
        if((g.keys&0x80103)||(flags&0x70))g.application_state=(g.config&0x2000)?2:4;
        if(live_time==3840){if(!host.notice(5,60,49))return -2;}
        else if(live_time==3900)g.application_state=(g.config&0x2000)?2:4;
    }
    root_score_display(hud,g);
    if(r.get(0x80)&0x70)return 3;
    if(!host.animate_backgrounds())return -2;++g.frames;++g.scene_frames;
    const u32 old=r.get(0x14),token=r.get(0x1c);float rate=1;if(token&&!host.timer_rate(token,rate))return -2;
    const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float elapsed=r.floating(0x18)+(unit?1.f:rate);
    r.put(0x10,old);r.put(0x18,word(elapsed));r.put(0x14,unit?old+1:elapsed>=-2147483648.f&&elapsed<2147483648.f?u32(i32(elapsed)):0x80000000);return 1;
}
}
