#include "TitleSceneReturn.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
void clock(AnmView title){auto t=title.sub(0x2b4);if(!(t.get(16)&1)){t.put(16,t.get(16)|1);t.put(12,0x4e40b0);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
bool clear(AnmView title,AnmResourceWorld& world,u32 script){const u32 at=0x2c8+script*4;if(at+4>GameTitleRuntime::bytes||!signal_animation(world,title.get(at),1,false))return false;title.put(at,0);return true;}
}
bool advance_title_scene_return(TitleScenePageBindings& b,SaveFileServices& files,GameSavedFile* loaded,u32& result){
    auto& owners=b.owners;auto& world=owners.world;auto title=owners.title.view();if(!owners.title.global_owner||title.get(0x1c)!=11||(title.get(0xe000)&1)||(title.get(0x24)!=3&&title.get(0x24)!=6))return false;
    if(title.get(0x24)==3){const u32 cheat=owners.cheat.view().get(0x2b0);if(signed_word(title.get(0x2b8))>=4&&(cheat==0||cheat==3)){if(!b.sound.title_sound(10))return false;title.put(0x24,2);clock(title);const u16 selected=u16(title.get(0x28)+7);if(!signal_animation(world,title.get(0x514),i32(std::int16_t(selected)),true))return false;}}
    else if(signed_word(title.get(0x2b8))>=6){b.equipment[2]=b.saved_equipment[2]=title.get(0x1d8);b.equipment[3]=b.saved_equipment[3]=title.get(0x28)-1;for(u32 script:{110u,title.get(0xe124),109u,114u,147u,159u})if(!clear(title,world,script))return false;u32 unused;if(!world.create_at(title.get(0x14),217,-1,{0,0,0},unused)||!signal_animation(world,title.get(0xdff4),1,false)||!signal_animation(world,title.get(0xdff8),1,false)||!owners.cheat.end_scene()||!signal_animation(world,title.get(0x73c),1,false))return false;title.put(0x73c,0);if(!select_title_state(owners.title,1))return false;MenuCursor{title.sub(0x28)}.pop();title.put(0xe000,title.get(0xe000)|0x10u);owners.application.put(0x998,1);if(!clear_title_dialog(owners.title,world)||!write_save_file(owners.save,b.saved_equipment,world,files,loaded))return false;}
    result=1;return consume_title_scene_responses(owners.title,world,b.png,b.saved)&&tick(title,world)&&world.synchronize_resources();
}
}
