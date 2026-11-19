#include "TitleSceneConfirm.hpp"
#include "RootTransition.hpp"
namespace th143 {
bool advance_title_scene_confirmation(TitleScenePageBindings& b,AnmMenuWorld& world,u32& result){
    auto& owners=b.owners;auto title=owners.title.view();if(!owners.title.global_owner||&owners.world!=&world||title.get(0x1c)!=11||title.get(0x24)!=4||(title.get(0xe000)&1)||signed_word(title.get(0x2b8))>=38)return false;
    if(title.get(0x2b8)==2){u32 resource=0,fade=0;if(!world.read(0x72bc7b0c+28*4,&resource,4)||!world.create_screen_transition(resource,fade)||!world.screen_transition_signal(fade,7))return false;owners.globals.fade_handle=fade;owners.application.put(0x1d0,fade);auto ascii=owners.ascii.view();u32 handle=ascii.get(0x191ec);if(!root_transition(world,ascii.get(0x191e4),handle,480.f,392.f)||!owners.cheat.end_scene())return false;ascii.put(0x191ec,handle);}
    if(!consume_title_scene_responses(owners.title,world,b.png,b.saved))return false;auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);result=1;return world.synchronize_resources();
}
}
