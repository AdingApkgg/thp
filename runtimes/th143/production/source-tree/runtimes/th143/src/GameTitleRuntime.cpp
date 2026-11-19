#include "GameTitleRuntime.hpp"
namespace th143 {
bool GameTitleRuntime::create(u32& result){
    result=0;if(global_owner||!storage.reserve_game_owner(self,bytes))return false;
    //45ed30 clears the whole object after the cursor/worker/text constructors.
    data.fill(0);auto owner=view();owner.put(4,2);global_owner=self;presentation=0;
    owner.put(0xe110,0x45ef60);owner.put(0xe108,1);owner.put(0xe104,0);
    u32 id=owner.get(0xe100),handle=0;if(!platform.launch_worker(0x45ef60,self,0,id,handle))return false;owner.put(0xe100,id);owner.put(0xe0fc,handle);result=self;return true;
}
}
