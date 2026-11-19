#include "GameMenuAnmRender.hpp"
namespace th143 {
bool GameMenuAnmRender::read_render_memory(u32 p,void* out,u32 n){if(p>=0x4e47d0&&std::uint64_t(p)+n<=std::uint64_t(0x4e47d0)+render.application.size()){std::memcpy(out,render.application.data()+p-0x4e47d0,n);return true;}return world.read(p,out,n)||device.read_game_render_memory(p,out,n);}
bool GameMenuAnmRender::write_render_memory(u32 p,const void* in,u32 n){return world.write(p,in,n)||device.write_game_render_memory(p,in,n);}
bool GameMenuAnmRender::draw_callback(u32 entry,AnmView vm){if(entry!=0x40a380)return false;auto* data=world.transition_data(vm.get(0x5b4));return data&&GameAnmEffect0Draw{render,device,world}.draw(data,i32(width),i32(height));}
bool GameMenuAnmRender::draw_pool_callback(u32 entry){
    const u32 layer=entry==0x4833f0?37:entry==0x483410?40:entry==0x483420?41:0;if(!layer)return render.draw_pool_callback(entry);u32 token;if(!world.read(0x72fe87b8+layer*AnmView::bytes,&token,4))return false;
    for(u32 budget=0;token;){if(++budget>1000000)return false;auto vm=world.state(token);if(!vm.data)return false;if(!(vm.get(0x1c)&0x20)){
        if(vm.get(0x5bc)!=0x40a380){if(!render.draw_player_visual(token,vm))return false;}
        else{auto app=AnmView{render.application.data()};const u32 camera=app.get(0x6e0);if(camera<0x4e47d0||std::uint64_t(camera)+300>std::uint64_t(0x4e47d0)+render.application.size())return false;++render.submitted;const i32 result=draw_anm_sprite(0x72000000,0x72000000,vm,{render.application.data()+camera-0x4e47d0},render.quad,world.viewport,render.drawing.depth_test,*this,device,*this);render.depth_test=render.drawing.depth_test;app.put(0xa04,render.depth_test);app.put(0xa00,render.drawing.depth_write);if(result==-2){render.error=token;return false;}}
    }token=vm.get(0x590);}return true;
}
}
