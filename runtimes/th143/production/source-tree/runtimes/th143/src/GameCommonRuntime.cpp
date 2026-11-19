#include "GameCommonRuntime.hpp"
namespace th143 {
bool GameCommonRuntime::create(u32& result){
    result=0;if(global_owner||!storage.reserve_game_owner(self,bytes))return false;
    // The native factory's memset wipes its preceding worker and inline-VM
    // constructors, including their vtables; none of those bytes survive.
    data.fill(0);global_owner=self;auto o=view();o.put(0,2);
    for(auto c:{std::array<u32,4>{0x4436a0,8,3,0},{0x4436b0,12,65,1}}){
        u32 p;if(!storage.allocate_game_storage(0x28,p)||!p||!frames.scheduler.create(p,c[0],storage.game_allocation_fill()))return false;
        auto cb=frames.scheduler.at(p);cb.put(4,cb.get(4)&~2u);cb.put(0x24,self);u32 ignored;if(!frames.scheduler.add(p,i32(c[2]),c[3]!=0,*this,ignored))return false;o.put(c[1],p);
    }
    //403e90 sees the freshly cleared +14 handle and returns immediately.
    o.put(0x28,0x4430b0);o.put(0x20,1);o.put(0x1c,0);
    u32 id=o.get(0x18),handle=0;if(!platform.launch_worker(0x4430b0,self,0,id,handle))return false;o.put(0x18,id);o.put(0x14,handle);
    result=self;return true;
}
bool GameCommonRuntime::update(AnmView app,ApplicationTargetGlobals& targets,CommonApplicationGlobals& g,AnmRenderMemory& memory,ApplicationTargetServices& graphics,GameAsciiRuntime& ascii,u32& result){
    if(!global_owner)return false;auto o=view();result=1;
    if(o.get(0)&2u){
        if(!initialize_application_targets(app,targets,memory,graphics))return false;
        g.presentation=1;if(!ascii.activate())return false;app.put(0x724,app.get(0x724)&~0x2000u);app.put(0x6ec,4);o.put(0,o.get(0)&~2u);
    }return true;
}
}
