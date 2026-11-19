#include "TitleReturnActivation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
void clock(AnmView title,u32 value){auto t=title.sub(0x2b4);if(!(t.get(16)&1)){t.put(16,t.get(16)|1);t.put(12,0x4e40b0);}t.put(0,value-1);t.put(4,value);t.put(8,word(float(signed_word(value))));}
bool tick(AnmView title,AnmResourceWorld& world){auto timer=title.sub(0x2b4);const u32 previous=timer.get(4),token=timer.get(12);float rate=1;if(token&&!world.timer_rate(token,rate))return false;timer.put(0,previous);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(8,word(value));timer.put(4,unit?previous+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
bool spawn(AnmView title,AnmResourceWorld& world,u32 script,u32 at){u32 handle;if(!world.create_at(title.get(0x14),i32(script),-1,{0,0,0},handle))return false;title.put(at,handle);return true;}
bool preview_worker(AnmView title,RootFactoryHost& host){auto w=title.sub(0xe0f8);u32 budget=100000;if(w.get(4)){w.put(12,1);w.put(16,0);u32 result;if(!host.wait_worker(w.get(4),200,result))return false;while(result==0x102){if(!budget--)return false;w.put(12,1);w.put(16,0);if(!host.sleep_worker(1)||!host.wait_worker(w.get(4),200,result))return false;}if(!host.close_worker(w.get(4)))return false;w.put(4,0);w.put(24,0);}w.put(24,0x464b20);w.put(16,1);w.put(12,0);u32 id=w.get(8),handle=0;if(!host.launch_worker(0x464b20,GameTitleRuntime::self,0,id,handle))return false;w.put(8,id);w.put(4,handle);return true;}
}
static bool enter_returned_scene_page(TitleSceneEntryBindings& b,u32& result){
    auto& t=b.title;auto title=t.title.view(),save=t.save.view();if(!t.title.global_owner||title.get(0x1c)!=11||title.get(0x24)||(title.get(0xe000)&0x20)||title.get(0xe940)||title.get(0xef58)||title.get(0xe328))return false;
    const u32 day=save.get(0xf084);if(day>9)return false;static constexpr u32 starts[]={1,7,13,20,27,35,43,51,58,66},counts[]={6,6,7,7,8,8,8,7,8,10};
    if(day<9){u32 cleared=0;for(u32 i=0;i<counts[day];++i)if(signed_word(save.get(0x40+(starts[day]+i)*0x314))>0)++cleared;if(cleared>=4){const u32 pending=save.get(0xf16c);if(pending>=16)return false;save.put(0xf084,day+1);save.put(0xf170+pending*4,day+30);save.put(0xf16c,pending+1);}}
    u32 primary=b.saved_equipment[0];if(!save.data[0xefac]&&primary==4){b.equipment[0]=b.saved_equipment[0]=primary=0;}if(save.data[0xefac]<=1&&primary==6)b.equipment[0]=b.saved_equipment[0]=0;
    if(!save.data[0xf08a]&&save.data[0xefad]){save.data[0xefad]=0;b.alternate=0;}
    title.put(0x30,11);MenuCursor main{title.sub(0x28)},days{title.sub(0x1d8)},mode{title.sub(0x100)};if(!main.select(b.reset_selection?0:signed_word(b.saved_equipment[3]+1)))return false;if(b.reset_selection)b.reset_selection=0;title.put(0x1e0,save.get(0xf084)+1);if(!days.select(signed_word(b.saved_equipment[2])))return false;title.put(0x2a8,0);title.put(0x108,2);if(!mode.select(0))return false;
    for(u32 script:{147u,110u,109u,114u})if(!spawn(title,t.world,script,0x2c8+script*4))return false;const u32 label=save.data[0xefac]==0?112:save.data[0xefac]==1?113:111;if(!spawn(title,t.world,label,0x2c8+label*4))return false;title.put(0xe124,label);
    if(!spawn(title,t.world,217,0xdff4)||!spawn(title,t.world,217,0xdff8)||!signal_animation(t.world,title.get(0xdff8),7,true))return false;
    for(u32 at:{0xdff4u,0xdff8u}){auto vm=t.world.find(title.get(at));if(!vm.data)return false;vm.put(0x1c,vm.get(0x1c)|0x800u);}
    auto cheat=t.cheat.view();cheat.put(0x484,word(400.f));cheat.put(0x488,word(528.f));cheat.put(0x48c,0);if(cheat.get(0x2b0)&&!t.cheat.position())return false;CheatSceneGlobals gear;gear.alternate=b.alternate;gear.primary=b.equipment[0];gear.secondary=b.equipment[1];gear.unlock=save.data[0xefac];gear.selection={0,6,3,1,7,4,2,5,8};if(!t.cheat.begin_scene(0,gear))return false;
    if(!title.get(0x73c)){u32 handle;if(!t.world.create_at(t.ascii.view().get(0x191e4),19,-1,{0,0,0},handle))return false;title.put(0x73c,handle);}
    if(!t.world.find(title.get(0x454)).data){if(!spawn(title,t.world,99,0x454)||!signal_animation(t.world,title.get(0x454),3,true))return false;}if(!signal_animation(t.world,title.get(0x454),title.get(0x28)?8:7,true))return false;
    title.put(0xe000,title.get(0xe000)&~0x10u);for(auto field:{std::array<u32,2>{0xe32c,5},{0xe534,5},{0xe73c,5},{0xe944,128},{0xeb4c,5},{0xed54,5},{0xef5c,128}})title.put(field[0],field[1]);if(!preview_worker(title,b.worker))return false;
    title.put(0x24,1);clock(title,0);clock(title,title.get(0xe000)&0x40?u32(-12):18);if(!spawn(title,t.world,159,0x544))return false;
    result=1;return tick(title,t.world)&&t.world.synchronize_resources();
}
namespace {
bool return_hide_resource(AnmResourceWorld& w,u32 resource){for(u32 head:{w.instances.registry.primary_head,w.instances.registry.secondary_head}){u32 budget=0;for(u32 node=head;node;){auto i=w.instances.registry.nodes.find(node-0x570);if(i==w.instances.registry.nodes.end()||++budget>1000000)return false;auto vm=i->second;if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20u);node=vm.get(0x574);}}return true;}
bool return_enable(TitleActivationBindings& b,AnmView owner,u32 field){auto cb=b.frames.scheduler.at(owner.get(field));if(!cb.data)return false;cb.put(4,cb.get(4)|2u);return true;}
}
bool advance_title_return_main_music(TitleActivationBindings& b){
    auto title=b.title.view();if(!(title.get(0xe000)&1))return true;title.put(0xdffc,title.get(0xdffc)+1);if(signed_word(title.get(0xdffc))<10)return true;
    MusicCommandQueue q;std::memcpy(q.data.data(),b.audio.data+0x24f8,q.data.size());const bool option=(b.application.get(0x20c)&0x10)!=0;MusicScene music;
    if(!q.enqueue(option?4:3,0,"dummy"))return false;b.audio.data[0x23f8]=0;if(!music.load(q,"th143_01"))return false;if(option&&!q.enqueue(4,0,"dummy"))return false;if(!q.enqueue(2,0,"dummy"))return false;
    std::memcpy(b.audio.data+0x24f8,q.data.data(),q.data.size());b.save.data[0xef74]=1;title.put(0xe000,title.get(0xe000)&~1u);title.put(0xdffc,0);return true;
}
bool tick_title_return_main_wait(TitleActivationBindings& b,u32& result){auto title=b.title.view();if(title.get(0x1c)!=11||title.get(0x24)!=1||!(title.get(0xe000)&1)||signed_word(title.get(0x2b8))>=10)return false;result=1;return tick(title,b.world)&&b.world.synchronize_resources();}
bool activate_returned_title_main(TitleSceneEntryBindings& entry,AnmMenuWorld& menu,u32& result){
    auto& b=entry.title;auto title=b.title.view();auto& g=b.globals;if(!b.title.global_owner||!b.cheat.global_owner||!b.ascii.global_owner||!b.application.data||!b.audio.data||&b.world!=&menu||title.get(0x1c)||g.return_mode!=1||!advance_title_return_main_music(b))return false;
    auto ascii=b.ascii.view();u32 fade=b.application.get(0x1d0);
    if(b.world.find(fade).data){if(!signal_animation(b.world,ascii.get(0x191e8),1,false)||!signal_animation(b.world,ascii.get(0x191ec),1,false))return false;ascii.put(0x191ec,0);if(!menu.screen_transition_signal(fade,1))return false;title.put(0xe000,title.get(0xe000)|0x40u);}
    b.application.put(0x1d0,0);g.fade_handle=0;if(!signal_animation(b.world,ascii.get(0x191ec),1,false))return false;ascii.put(0x191ec,0);
    if(g.trophy_owner)return false;auto save=b.save.view();const i32 pending=signed_word(save.get(0xf16c));if(pending>0&&(pending>16||save.get(0xf16c+u32(pending)*4)==39))return false;
    for(u32 slot:{5u,7u,2u,0u}){u32 resource;if(!b.world.read(0x72bc7b0c+slot*4,&resource,4)||!return_hide_resource(b.world,resource))return false;}
    if(!return_enable(b,b.cheat.view(),8)||!return_enable(b,b.cheat.view(),12))return false;
    if(g.startup_flags&0x80){title.put(0xe000,title.get(0xe000)&~1u);g.game_state=g.cached_game_state;}else{title.put(0xe000,title.get(0xe000)|1u);title.put(0xdffc,0);}g.startup_flags&=~0x80u;title.put(0xe000,title.get(0xe000)|2u);
    MusicCommandQueue q;std::memcpy(q.data.data(),b.audio.data+0x24f8,q.data.size());MusicScene music;if(!music.load(q,"th143_01")||!q.start(b.save,0,0,b.application.get(0x20c)))return false;std::memcpy(b.audio.data+0x24f8,q.data.data(),q.data.size());
    if(!return_enable(b,title,16))return false;g.return_mode=1;if(!select_title_state(b.title,1))return false;return advance_title_main_intro(b.title,b.world,result);
}

}
