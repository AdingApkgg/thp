#include "CheatInitialize.hpp"
namespace th143 {
bool initialize_cheat_owner(AnmView owner,u32 self,Scheduler& scheduler,CheatInitializeHost& host,i32& result){
    u32 resource;if(!host.cheat_resource(26,"itemequip.anm",resource))return false;owner.put(0x10,resource);
    if(!resource){if(!host.cheat_resource_error())return false;result=-1;return true;}
    for(auto entry:{std::array<u32,4>{0x438330,7,0,8},{0x438340,67,1,12}}){
        u32 token;u8 fill;
        if(!host.cheat_callback_storage(token,fill)||!scheduler.create(token,entry[0],fill))return false;
        auto callback=scheduler.at(token);callback.put(4,callback.get(4)&~2u);callback.put(0x24,self);
        u32 ignored;if(!scheduler.add(token,i32(entry[1]),entry[2]!=0,host,ignored))return false;
        owner.put(entry[3],token);
    }
    set_cheat_state(owner,0);result=0;return true;
}
}
