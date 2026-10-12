#include "../../cpp/game/AnmManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource;static u32 id,before,after;
API(run) i32 run(u32 overlay,u32 layer,u32 state){
 manager.clear();resource={};resource.scripts.resize(1);resource.scripts[0].bytes.resize(16);const AnmInstruction commands[]={{2,8,0,0},{-1,8,0,0}};std::memcpy(resource.scripts[0].bytes.data(),commands,16);
 auto* vm=manager.create(resource,0,0,layer,overlay);if(!vm)return -1;id=vm->id;before=layer;vm->flags2=state;
 if(!manager.update(overlay))return -2;vm=manager.find(id);after=vm?vm->layer:before;return 0;
}
API(after_layer) u32 after_layer(){return after;}
API(linked_layer) i32 linked_layer(){for(u32 n=0;n<43;++n)if(auto* vm=manager.layer_first(n);vm&&vm->id==id)return i32(n);return -1;}
API(alive) u32 alive(){return manager.find(id)!=nullptr;}
