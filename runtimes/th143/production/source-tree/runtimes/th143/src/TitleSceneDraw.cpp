#include "TitleSceneDraw.hpp"
#include "CheatAnimation.hpp"
#include "AsciiFormat.hpp"
#include <cstdio>
namespace th143 {
namespace {
AnmView child(AnmView title,AnmResourceWorld& world,u32 parent,i32 script){const u32 slot=0x2c8+parent*4;if(slot+4>0xef78)return {nullptr};auto vm=world.find(title.get(slot));if(!vm.data){title.put(slot,0);return {nullptr};}return find_animation_child(world,vm,script);}
bool position(AnmView vm,AnmResourceWorld& world,float offset,std::array<float,3>& p){if(!vm.data||!anm_position(vm,world.viewport,world,p))return false;p[0]=(world.viewport.scale*offset+p[0])/world.viewport.scale;p[1]/=world.viewport.scale;return true;}
}
bool draw_title_scene_page(GameTitleRuntime& owner,GameAsciiRuntime& ascii,SaveData& save,AnmResourceWorld& world){
    auto title=owner.view(),a=ascii.view(),s=save.view();if(title.get(0x24)!=2&&title.get(0x24)!=3)return true;a.put(0x191c8,4);std::array<float,3> p;
    if(signed_word(title.get(0x28))>=1){static constexpr u32 starts[]={1,7,13,20,27,35,43,51,58,66};const u32 day=title.get(0x1d8),selection=title.get(0x28);if(day>=10||selection>10)return false;const u32 record=(starts[day]+selection-1)*0x314,values[]={s.get(record+0x40),s.get(record+0x6c),s.get(record+0x70)*10};for(u32 i=0;i<3;++i)if(!position(child(title,world,title.get(0xe124),i32(156+i)),world,96.f,p)||!queue_ascii_text(a,p,format_ascii_number(values[i]),world.viewport))return false;
    }else {
        auto vm=child(title,world,159,160);if(!vm.data)return false;a.data[0x191b3]=vm.data[0x537];if(!position(vm,world,136.f,p))return false;const i32 ticks=signed_word(s.get(0xef94));char text[96];const int n=std::snprintf(text,sizeof text,"%d:%.2d:%.2d",ticks/360000,(ticks/6000)%60,(ticks/100)%60);if(n<0||n>=int(sizeof text)||!queue_ascii_text(a,p,std::string_view(text,u32(n)),world.viewport))return false;
        if(!position(child(title,world,159,161),world,136.f,p)||!queue_ascii_text(a,p,std::to_string(signed_word(s.get(0xef2c))),world.viewport))return false;u32 trophies=0;for(u32 i=0;i<70;++i)if(s.data[0xeff9+i])++trophies;if(!position(child(title,world,159,162),world,136.f,p)||!queue_ascii_text(a,p,std::to_string(trophies),world.viewport))return false;a.data[0x191b3]=255;
    }
    a.put(0x191c8,0);return true;
}
}
