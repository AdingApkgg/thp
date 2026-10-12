#include "HudTh14Text.hpp"
#include "Th14LifeFragments.hpp"
#include "SpellTiming.hpp"
#include <cstdio>
#include <algorithm>
namespace th11 {
#if PORT_TITLE == 14
namespace {
void grouped(char* out,u32 value){
    if(value<1000)std::snprintf(out,64,"%u",value);
    else if(value<1000000)std::snprintf(out,64,"%u,%03u",value/1000,value%1000);
    else if(value<1000000000)std::snprintf(out,64,"%u,%03u,%03u",value/1000000,value/1000%1000,value%1000);
    else std::snprintf(out,64,"%u,%03u,%03u,%03u",value/1000000000,value/1000000%1000,value/1000%1000,value%1000);
}
void score_text(char* out,u32 value,i32 continues){
    if(value<100)std::snprintf(out,64,"%d",signed_bits(value*10u+u32(continues)));
    else if(value<100000)std::snprintf(out,64,"%u,%02u%d",value/100,value%100,continues);
    else if(value<100000000)std::snprintf(out,64,"%u,%03u,%02u%d",value/100000,value/100%1000,value%100,continues);
    else std::snprintf(out,64,"%u,%03u,%03u,%02u%d",value/100000000,value/100000%1000,value/100%1000,value%100,continues);
}
}
bool th14_hud_awards(AsciiText& output,const Th14HudAwards& data){
    // Retail431140..43144a: grouped result bonus and two spell-time rows.
    AsciiStyle style;style.font=4;style.pass=2;char text[64];
    if(data.result){
        grouped(text,u32(data.bonus));style.color=u32(data.result_alpha)<<24|0xffffff;
        float x=224;for(const char* p=text;*p;++p)x-=float(*p==','?4:12)*.5f;
        if(!output.add(text,{x,200,0},style))return false;
    }
    if(data.time){
        const auto best=decode_spell_time(data.encoded);
        for(u32 row=0;row<2;++row){
            style.scale={1,1};style.color=u32(data.time_alpha)<<24|(row?0x808080:0xffffff);
            const i32 sec=row?best.seconds:std::min(data.frames/60,999),hund=row?best.hundredths:signed_bits(u32(data.frames%60)*100u)/60;
            std::snprintf(text,sizeof text,"%3d.",sec);if(!output.add(text,{224,row?224.f:208.f,0},style))return false;
            style.scale={.6f,.6f};std::snprintf(text,sizeof text,"%.2ds",hund);if(!output.add(text,{268,row?230.f:214.f,0},style))return false;
        }
    }return true;
}
bool th14_hud_counters(AsciiText& output,const GameEconomy& e,const HudScore& score,u8 alpha){
    // Retail 43144a..4318b6 and the grouping helpers 40bb60/40bc70.
    // Convert native right alignment to the shared queue's left origin using
    // the original per-character float subtraction, including narrow commas.
    AsciiStyle style;style.font=4;style.color=u32(alpha)<<24|0x808080;char text[64];
    auto put=[&](float x,float y,bool right=false){if(right)for(const char* p=text;*p;++p)x-=style.scale.x*float(*p==','?4:12);return output.add(text,{x,y,0},style);};
    score_text(text,u32(score.high),score.high_continues);if(!put(620,44,true))return false;
    style.color=u32(alpha)<<24|0xffffff;score_text(text,u32(score.displayed),score.continues);if(!put(620,66,true))return false;
    style.scale={.6f,.6f};const i32 required=th14_life_fragment_requirement(e.th14_life_awards);
    if(required>=999999){std::snprintf(text,sizeof text,"---/---");if(!put(569,122)||!put(576,160))return false;}
    else{
        std::snprintf(text,sizeof text,"%3d",e.life_fragments);if(!put(576,122))return false;
        std::snprintf(text,sizeof text,"/%d",required);if(!put(597,122))return false;
        std::snprintf(text,sizeof text,"%3d",e.th14_bomb_fragments);if(!put(576,160))return false;
        std::snprintf(text,sizeof text,"/8");if(!put(597,160))return false;
    }
    if(!e.power_step)return false;
    style.color=u32(alpha)<<24|0xff8030;style.scale={1,1};std::snprintf(text,sizeof text,"%d.",e.power/e.power_step);if(!put(540,216))return false;
    style.scale={.6f,.6f};std::snprintf(text,sizeof text,"%.2d",signed_bits(u32(e.power%e.power_step)*100u)/e.power_step);if(!put(560,223))return false;
    style.scale={1,1};std::snprintf(text,sizeof text,"/%d.",e.max_power/e.power_step);if(!put(574,216))return false;
    style.scale={.6f,.6f};std::snprintf(text,sizeof text,"00");if(!put(606,223))return false;
    style.scale={1,1};style.color=u32(alpha)<<24|0x40c0ff;const i32 points=e.point_value/100;grouped(text,u32(points-points%10));if(!put(620,238,true))return false;
    style.color=u32(alpha)<<24|0x808080;grouped(text,u32(e.graze));return put(620,260,true);
}
#endif
}
