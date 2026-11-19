#include "ResultsMenuDraw.hpp"
#include <cmath>
namespace th143 {
namespace {float divide(float a,float b){return a==0.f&&b==0.f?real(0xffc00000):a/b;}}
bool draw_results_menu(AnmView menu,AnmView save,AnmView ascii,const ResultsMenuDrawGlobals& globals,ResultsMenuDrawHost& host){
    const u32 page=menu.get(0x3ec);
    if(page==7||page==8)return host.results_subpage(page==7?0x449780:0x449890,menu);
    if(page!=1)return true;if(globals.scene>=76)return false;
    ascii.put(0x191c8,4);
    const u32 values[]={save.get(globals.scene*0x314+0x40),save.get(globals.scene*0x314+0x6c),globals.score*10u,globals.graze};
    for(u32 i=0;i<4;++i){u32 parent=menu.get(0x91b8);std::array<float,3> position;
        if(!host.results_child_position(parent,i32(233+i),position))return false;menu.put(0x91b8,parent);
        const float offset=globals.scale*96.f;position[0]=divide(offset+position[0],globals.scale);position[1]=divide(position[1],globals.scale);
        if(!host.results_number(position,values[i]))return false;
    }
    ascii.put(0x191c8,0);return true;
}
}
