#include "GameApplicationFinalDraw.hpp"
namespace th143 {
bool finish_game_application_draw(GameRenderRuntime& render,GameRenderDevice& device,AnmView menu,u32 independent_signals){
    if(independent_signals&3u)return false;
    if(!render.flush())return false;auto app=AnmView{render.application.data()};for(u32 at:{0x6b0u,0x6b4u,0x458u,0x45cu})app.put(at,0);
    if(!menu.data||!(menu.get(0x91bc)&1u))return true;
    const u32 token=device.game_device_token();if(!device.application_render_target(token,0,app.get(0x1ac))||!device.render_state(15,0))return false;
    for(u32 at:{0x404u,0x9d0u}){auto vm=menu.sub(at);vm.put(0x534,0xffffffff);if(!render.draw_player_visual(0x6b020000+at,vm))return false;}
    if(!render.flush()||!device.render_state(15,1)||!device.application_render_target(token,0,app.get(0x1b4)))return false;
    menu.put(0x91bc,menu.get(0x91bc)&~1u);return true;
}
}
