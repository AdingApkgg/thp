#include "StageCleanup.hpp"
namespace th143 {
bool cleanup_stage(StageState& state,u32 self,StageCleanupGlobals& g,StageCleanupHost& host){
    auto s=state.view();
    for(u32 at:{8,12,0x4268})if(s.get(at)&&!host.remove_stage_callback(s.get(at)))return false;
    auto release_field=[&](u32 at){const u32 p=s.get(at);if(p&&!host.release_stage_storage(p,true))return false;s.put(at,0);return true;};
    auto release_vm=[&](u32 vm){u32 extra;if(!host.read_stage_cleanup_memory(vm+0x5b4,&extra,4))return false;if(extra&&!host.release_stage_storage(extra,true))return false;const u32 zero=0;return host.write_stage_cleanup_memory(vm+0x5b4,&zero,4);};
    if(s.get(0x208)){
        for(i32 i=0;;++i){std::int16_t count;if(!host.read_stage_cleanup_memory(s.get(0x10)+2,&count,2))return false;if(i>=count)break;if(!release_vm(s.get(0x208)+u32(i)*0x5cc))return false;}
        if(!release_field(0x208))return false;
    }
    if(!release_field(0x10)||!release_field(0x426c))return false;s.put(0x426c,0);
    const u32 collection=s.get(0x4244);
    if(collection){if(!host.cleanup_stage_collection(collection)||!host.release_stage_storage(collection,false))return false;s.put(0x4244,0);}
    if(!(g.game_flags&1)&&!host.unload_stage_animation((s.get(0x423c)&1)+3))return false;
    if(g.current==self)g.current=0;if(g.previous==self)g.previous=0;
    for(u32 i=3;i;--i){const u32 at=0x30b4+(i-1)*0x5cc+0x5b4;const u32 p=s.get(at);if(p&&!host.release_stage_storage(p,true))return false;s.put(at,0);}
    for(u32 i=8;i;--i){const u32 at=0x20c+(i-1)*0x5cc+0x5b4;const u32 p=s.get(at);if(p&&!host.release_stage_storage(p,true))return false;s.put(at,0);}
    return true;
}
}
