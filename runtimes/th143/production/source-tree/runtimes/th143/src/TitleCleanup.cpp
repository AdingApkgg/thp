#include "TitleCleanup.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
struct Callbacks:SchedulerHost {
    GameOwnerServices& storage;explicit Callbacks(GameOwnerServices& s):storage(s){}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return storage.release_game_storage(p);}
};
bool stop(AnmView title,RootFactoryHost& host,u32& budget){auto w=title.sub(0xe0f8);if(!w.get(4))return true;w.put(12,1);w.put(16,0);u32 result;if(!budget--||!host.wait_worker(w.get(4),200,result))return false;while(result==0x102){w.put(12,1);w.put(16,0);if(!host.sleep_worker(1)||!budget--||!host.wait_worker(w.get(4),200,result))return false;}if(!host.close_worker(w.get(4)))return false;w.put(4,0);w.put(24,0);return true;}
bool preview_arrays(AnmView title,AnmResourceWorld& world){auto q=title.sub(0xe330);while(q.get(0x200)){u32 token=0;if(signed_word(q.get(0x200))>0){token=q.get(0);q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}if(!world.release_enemy_storage(token,true))return false;}return true;}
}
bool destroy_title(TitleLoadBindings& b,RootFactoryHost& worker,TitleReplayCleanupHost* replays,u32 budget){
    if(!b.title.global_owner)return true;auto title=b.title.view();if(title.get(0xed50)||title.get(0xe530)>128)return false;if(!replays)for(u32 i=0;i<100;++i)if(title.get(0x5b54+i*4))return false;
    title.put(0,0x4c7f04);title.put(0xe000,title.get(0xe000)|0x10u);if(!stop(title,worker,budget))return false;Callbacks callbacks{b.storage};for(u32 at:{12,16})if(title.get(at)&&!b.frames.scheduler.remove(title.get(at),callbacks))return false;
    for(u32 slot:{16,17})if(!b.resources.unload(slot))return false;for(u32 i=0;i<100;++i)if(u32 replay=title.get(0x5b54+i*4))if(!replays->cleanup_title_replay(replay)||!b.storage.release_game_storage(replay))return false;
    if(!signal_animation(b.resources,title.get(0x73c),1,false))return false;title.put(0xe000,title.get(0xe000)|0x10u);if(!stop(title,worker,budget)||!preview_arrays(title,b.resources)||!b.cheat.destroy())return false;
    for(u32 at:{0x5ce4,0x5ce8}){const u32 token=title.get(at);if(token&&!b.resources.release_enemy_storage(token,true))return false;title.put(at,0);}b.title.global_owner=0;title.put(0xe0f8,0x4c4c64);return stop(title,worker,budget)&&b.storage.release_game_storage(GameTitleRuntime::self);
}
}
