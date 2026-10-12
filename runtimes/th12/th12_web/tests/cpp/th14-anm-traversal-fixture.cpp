#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource;static AnmVm* vms[6];static u32 ids[6],state[30],events[12],event_count,mutation,chains[36*7];
static u32 index(AnmVm* vm){if(!vm)return ~0u;for(u32 i=0;i<6;++i)if(vms[i]==vm)return i;return ~1u;}
static void callback(AnmVm& vm){events[event_count++]=index(&vm);auto* target=mutation==1?&vm:mutation==2&&vm.registry.next?vm.registry.next->value:nullptr;if(target)target->flags2|=0x20;}
API(begin) i32 begin(u32 order,u32 mode,u32 mask,u32 mutate,u32 layout){manager.clear();resource={};resource.scripts.resize(1);const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};resource.scripts[0].bytes.resize(sizeof code);std::memcpy(resource.scripts[0].bytes.data(),code,sizeof code);if(!manager.prepare_resource(resource,0))return 0;mutation=mutate;
 const u32 orders[2][6]={{0,1,2,3,4,5},{5,2,4,1,3,0}},normal_layers[6]={0,3,24,33,3,24},overlay_layers[6]={0,24,33,34,35,0};
 for(u32 k=0;k<6;++k){const u32 i=orders[order][k];const bool overlay=mode==2||(mode==1&&(i%2));vms[i]=manager.create(resource,0,0,24,overlay);if(!vms[i])return 0;ids[i]=vms[i]->id;vms[i]->flags2=0x200|((i%3)*0x40)|((mask&(1u<<i))?0x20:0);vms[i]->layer=layout?(overlay?overlay_layers[i]:normal_layers[i]):24;vms[i]->instruction=nullptr;vms[i]->before_update=callback;}
 const i32 parents[]={-1,0,1,0,3,3};for(u32 i=0;i<6;++i){auto& vm=*vms[i];vm.parent=parents[i]>=0?vms[parents[i]]:nullptr;vm.child.value=&vm;vm.child.previous=i?&vms[i-1]->child:nullptr;vm.child.next=i<5?&vms[i+1]->child:nullptr;}return 1;}
API(step) i32 step(){event_count=0;if(!manager.update(false)||!manager.update(true))return 0;
 for(u32 i=0;i<6;++i){auto* s=state+i*5;auto* vm=manager.find(ids[i]);if(!vm){for(u32 j=0;j<5;++j)s[j]=0;continue;}s[0]=1;s[1]=vm->flags2;s[2]=index(vm->parent);s[3]=vm->layer;s[4]=index(vm->draw_next);}
 for(u32 layer=0;layer<36;++layer){auto* s=chains+layer*7;u32 n=0;for(auto* vm=manager.layer_first(layer);vm;vm=vm->draw_next){if(n>=6)return 0;s[++n]=index(vm);}s[0]=n;}return 1;}
API(data) const u32* data(){return state;}
API(layer_data) const u32* layer_data(){return chains;}
API(event_data) const u32* event_data(){return events;}
API(count) u32 count(){return event_count;}
