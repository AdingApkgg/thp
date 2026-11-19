#include "CommonCleanup.hpp"
namespace th143 {
namespace {
bool stop(AnmView w,CommonCleanupHost& host,u32& budget){
    if(!w.get(4))return true;u32 result;
    w.put(12,1);w.put(16,0);if(!budget--||!host.wait_common_worker(w.get(4),200,result))return false;
    while(result==0x102){w.put(12,1);w.put(16,0);if(!host.sleep_common_worker(1)||!budget--||!host.wait_common_worker(w.get(4),200,result))return false;}
    if(!host.close_common_worker(w.get(4)))return false;w.put(4,0);w.put(24,0);return true;
}
struct Callbacks:SchedulerHost {
    GameOwnerServices& storage;explicit Callbacks(GameOwnerServices& s):storage(s){}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return storage.release_game_storage(p);}
};

}
bool destroy_common(CommonLoadBindings& b,CommonCleanupHost& host,u32 wait_budget){
    if(!b.common.global_owner)return true;auto o=b.common.view();if(!stop(o.sub(0x10),host,wait_budget))return false;
    Callbacks callbacks{b.storage};for(u32 at:{8,12})if(!b.frames.scheduler.remove(o.get(at),callbacks))return false;
    for(u32 slot:{5,7,8,26,9,27})if(!b.resources.unload(slot))return false;
    if(!b.auxiliary.destroy_effects()||!b.resources.unload(1))return false;
    b.common.global_owner=0;
    if(!b.ascii.destroy()||!b.resources.unload(0)||!b.save_owner||!write_save_file(b.save,b.saved_equipment,b.resources,host,b.loaded_save))return false;
    auto s=b.save.view();for(u32 at:{0,4}){const u32 p=s.get(at);if(p&&!b.resources.release_enemy_storage(p,true))return false;s.put(at,0);}
    if(!b.storage.release_game_storage(b.save_owner))return false;b.save_owner=0;
    const u32 geometry=o.get(0x5e4);if(geometry&&!b.resources.release_enemy_storage(geometry,true))return false;o.put(0x5e4,0);
    o.put(0x10,0x4c4c64);return stop(o.sub(0x10),host,wait_budget)&&b.storage.release_game_storage(GameCommonRuntime::self);
}
}
