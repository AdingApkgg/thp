#include "RootFactory.hpp"

namespace th143 {
bool stop_background_worker(BackgroundWorker& worker,RootFactoryHost& host,u32 budget){
    auto w=worker.view();if(!w.get(4))return true;
    w.put(12,1);w.put(16,0);u32 result;
    if(!budget--||!host.wait_worker(w.get(4),200,result))return false;
    while(result==0x102){
        w.put(12,1);w.put(16,0);
        if(!host.sleep_worker(1)||!budget--||!host.wait_worker(w.get(4),200,result))return false;
    }
    if(!host.close_worker(w.get(4)))return false;w.put(4,0);w.put(24,0);return true;
}
bool start_root_worker(BackgroundWorker& worker,RootFactoryHost& host){
    if(!stop_background_worker(worker,host))return false;auto w=worker.view();
    w.put(24,0x432a20);w.put(16,1);w.put(12,0);
    u32 id=w.get(8),handle=0;if(!host.launch_worker(0x432a20,0,0,id,handle))return false;
    w.put(8,id);w.put(4,handle);return true;
}
bool create_root(RootState& root,BackgroundWorker& worker,RootFactoryGlobals& g,u32 mode,RootFactoryHost& host){
    u32 token;if(!host.allocate_root(token)||!token)return false;
    root.construct();g.presentation=0;if(!host.evict_managed_textures())return false;
    root.view().put(0x80,root.view().get(0x80)|4);g.root=token;root.view().put(0x94,mode);
    return start_root_worker(worker,host);
}
}
