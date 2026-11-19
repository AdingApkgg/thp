#include "TitleDialog.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
bool clear_title_dialog(GameTitleRuntime& owner,AnmResourceWorld& world){auto title=owner.view();if(!signal_animation(world,title.get(0xdff4),3,true)||!signal_animation(world,title.get(0xdff8),3,true)||!world.mark_retirement(title.get(0xef64)))return false;title.put(0xef64,0);return world.synchronize_resources();}
bool show_title_dialog(GameTitleRuntime& owner,AnmResourceWorld& world,TitleDialogHost& host,const std::vector<u8>& first,const std::vector<u8>& second,float x,float y,float extent){
    if(!clear_title_dialog(owner,world))return false;auto title=owner.view();const u32 kind=!second.empty()&&second[0]=='\\'?1:9;u32 handle;if(!world.create_at(title.get(0x14),i32(266+kind),-1,{x,y,0},handle))return false;title.put(0xef64,handle);auto parent=world.find(handle);for(u32 base:{218u,250u}){auto child=find_animation_child(world,parent,i32(base+kind));if(!child.data)return false;child.put(0x4bc,word(extent));}title.put(0xef60,kind);
    auto text=[&](u32 at){auto vm=world.find(title.get(at));if(!vm.data)title.put(at,0);return vm;};const std::vector<u8> blank{32,32};
    if(!host.title_dialog_text(text(0xdff4),blank)||!host.title_dialog_text(text(0xdff8),blank)||!signal_animation(world,title.get(0xdff4),3,false)||!signal_animation(world,title.get(0xdff8),3,false)||!signal_animation(world,title.get(0xdff4),2,true)||!host.title_dialog_text(text(0xdff4),first))return false;
    if(kind==9&&(!host.title_dialog_text(text(0xdff8),second)||!signal_animation(world,title.get(0xdff8),2,true)))return false;
    const float text_x=x-(extent+64.f);for(u32 at:{0xdff4u,0xdff8u}){auto vm=text(at);if(vm.data){vm.put(0x59c,word(text_x));vm.put(0x5a0,word(y));vm.put(0x5a4,0);}}
    return world.synchronize_resources();
}
}
