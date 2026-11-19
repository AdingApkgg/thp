#include "GameTitleRootApplication.hpp"
namespace th143 {
namespace {
struct WorkerBridge:RootFactoryHost {
    AnmView application;BackgroundWorker& worker;RootFactoryGlobals& globals;u32& presentation;RootFactoryHost& next;
    WorkerBridge(AnmView a,BackgroundWorker& w,RootFactoryGlobals& g,u32& p,RootFactoryHost& n):application(a),worker(w),globals(g),presentation(p),next(n){}
    void publish(){std::memcpy(application.data+0x98c,worker.data.data(),worker.data.size());presentation=globals.presentation;}
    bool allocate_root(u32& p)override{return next.allocate_root(p);}
    bool evict_managed_textures()override{publish();return next.evict_managed_textures();}
    bool wait_worker(u32 h,u32 ms,u32& r)override{publish();return next.wait_worker(h,ms,r);}
    bool sleep_worker(u32 ms)override{publish();return next.sleep_worker(ms);}
    bool close_worker(u32 h)override{publish();return next.close_worker(h);}
    bool launch_worker(u32 entry,u32 argument,u32 flags,u32& id,u32& handle)override{publish();return next.launch_worker(entry,argument,flags,id,handle);}
};
}
bool GameTitleRootApplication::application_state_call(u32 entry,u32 ecx,u32 argument,u32& result){
    if(entry==0x45f6a0){result=0;return destroy_title(title,host,replays);}
    if(entry==0x432f00){if(!application.data)return false;std::memcpy(worker.data.data(),application.data+0x98c,worker.data.size());globals.presentation=presentation;WorkerBridge bridge{application,worker,globals,presentation,host};const bool ok=create_root(root,worker,globals,ecx,bridge);bridge.publish();result=globals.root;return ok;}
    return next.application_state_call(entry,ecx,argument,result);
}
}
