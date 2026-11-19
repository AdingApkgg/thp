#include "HudDraw.hpp"
#include <algorithm>
namespace th143 {
bool draw_hud_text(AnmView h,AnmView a,AnmView enemy,AnmView special,const HudDrawGlobals& g,AnmWorld& world){
    if(!h.data||!a.data)return false;
    auto find=[&](u32 at){auto vm=world.find(h.get(at));if(!vm.data)h.put(at,0);return vm;};
    auto text=[&](float x,float y,const std::string& s){return queue_ascii_text(a,{x,y,0},s,world.viewport);};
    auto formatted=[&](float x,float y,const char* f,i32 value){std::string s;return format_ascii_value(f,double(value),s)&&text(x,y,s);};
    auto vm=find(0x110);
    if(vm.data){a.data[0x191b3]=vm.data[0x537];a.put(0x191cc,2);a.put(0x191c8,4);a.put(0x191d4,0);a.put(0x191d8,0);
        if(!text(224,200,format_ascii_number(h.get(0x2b0))))return false;
        a.data[0x191b3]=255;a.put(0x191c8,0);a.put(0x191cc,0);a.put(0x191d4,1);a.put(0x191d8,1);
    }
    if(h.get(0x11c)){
        vm=find(0x118);
        if(!special.data){h.put(0x11c,0);if(!world.mark_retirement(h.get(0x118)))return false;h.put(0x118,0);}
        else if(!vm.data)h.put(0x11c,0);
        else{
            a.data[0x191b3]=vm.data[0x537];a.put(0x191cc,2);a.put(0x191c8,4);
            const i32 ticks=signed_word(special.get(0x94)),seconds=ticks/60;
            if(!formatted(224,208,"%3d.",std::min(seconds,999)))return false;
            a.put(0x191b4,word(.6f));a.put(0x191b8,word(.6f));
            if(!formatted(268,214,"%.2ds",signed_word(u32(ticks-seconds*60)*100)/60))return false;
            a.put(0x191b0,0xff808080);a.data[0x191b3]=vm.data[0x537];a.put(0x191b4,word(1.f));a.put(0x191b8,word(1.f));
            const i32 encoded=signed_word(special.get(0xa8));i32 best_seconds=(encoded/100%1000+934)%1000,best_hundredths=(encoded%100+67)%100;
            if(encoded/100000-22!=best_seconds+best_hundredths){best_seconds=999;best_hundredths=99;}
            if(!formatted(224,224,"%3d.",best_seconds))return false;
            a.put(0x191b4,word(.6f));a.put(0x191b8,word(.6f));if(!formatted(268,230,"%.2ds",best_hundredths))return false;
            a.data[0x191b3]=255;a.put(0x191b4,word(1.f));a.put(0x191b8,word(1.f));a.put(0x191c8,0);a.put(0x191cc,0);a.put(0x191b0,0xffffffff);
        }
    }
    a.put(0x191c8,4);a.put(0x191b0,0xff808080);
    vm=find(0x120);
    if(vm.data){auto child=find_animation_child(world,vm,6);if(!child.data)return false;a.data[0x191b3]=child.data[0x537];a.put(0x191d4,1);a.put(0x191d8,1);
        if(!text(160,16,format_ascii_score(g.high_score,g.high_score_scene)))return false;}
    a.put(0x191b0,0xffffffff);a.put(0x191d4,2);a.put(0x191d8,1);
    vm=find(0x120);
    if(vm.data){auto child=find_animation_child(world,vm,7);if(!child.data)return false;a.data[0x191b3]=child.data[0x537];if(!text(508,16,format_ascii_score(h.get(0x144),g.scene)))return false;}
    a.put(0x191b0,0xffffffff);a.put(0x191d4,1);a.put(0x191d8,1);a.data[0x191b3]=255;a.put(0x191c8,0);a.put(0x191cc,0);
    if(enemy.data&&signed_word(h.get(0x1a0))>=0&&enemy.get(0x5c)&&!(enemy.get(0x9c)&1)&&!h.get(0x198)){
        auto clock=world.state(h.get(0x98));if(!clock.data)return false;const float x=clock.floating(0x3c)+16.f,y=clock.floating(0x40)-7.f;
        a.put(0x191b0,clock.get(0x534));a.put(0x191c8,4);a.put(0x191cc,2);if(!text(x,y,"."))return false;
        a.put(0x191b4,word(.6f));a.put(0x191b8,word(.6f));if(!formatted(x+8.f,y+6.f,"%.2d",signed_word(h.get(0x1a4))))return false;
        a.put(0x191b4,word(1.f));a.put(0x191b8,word(1.f));a.put(0x191b0,0xffffffff);a.put(0x191cc,0);a.put(0x191c8,0);
    }return true;
}
}
