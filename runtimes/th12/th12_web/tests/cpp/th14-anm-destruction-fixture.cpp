#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource;static AnmVm* vms[6];static u32 ids[6],state[46];
static u32 index(AnmVm* vm){if(!vm)return ~0u;for(u32 i=0;i<6;++i)if(vms[i]==vm)return i;return ~1u;}
static u32 node_index(AnmVm::Node* node){return node?index(node->value):~0u;}
API(begin) i32 begin(u32 mode){manager.clear();resource={};resource.scripts.resize(1);const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};resource.scripts[0].bytes.resize(sizeof code);std::memcpy(resource.scripts[0].bytes.data(),code,sizeof code);if(!manager.prepare_resource(resource,0))return 0;
 for(u32 i=0;i<6;++i){vms[i]=manager.create(resource,0,0,24,mode==2||(mode==1&&(i%2)));if(!vms[i])return 0;ids[i]=vms[i]->id;vms[i]->flags2=0x200|((i%3)*0x40);}
 const i32 parents[]={-1,0,1,0,3,3};for(u32 i=0;i<6;++i){auto& vm=*vms[i];vm.parent=parents[i]>=0?vms[parents[i]]:nullptr;vm.child.value=&vm;vm.child.previous=i?&vms[i-1]->child:nullptr;vm.child.next=i<5?&vms[i+1]->child:nullptr;}return 1;}
API(erase) const u32* erase(u32 selected){manager.destroy(*vms[selected]);
 for(u32 i=0;i<6;++i){auto* s=state+i*7;auto* vm=manager.find(ids[i]);if(!vm){for(u32 j=0;j<7;++j)s[j]=0;continue;}s[0]=1;s[1]=vm->flags2;s[2]=index(vm->parent);s[3]=node_index(vm->child.next);s[4]=node_index(vm->child.previous);s[5]=node_index(vm->registry.next);s[6]=node_index(vm->registry.previous);
 }
 // Registry endpoints are exposed from each live node; the mode maps their
 // original membership without reaching into AnmManager's private storage.
 return state;}
static u32 current_mode;
API(start) i32 start(u32 mode){current_mode=mode;return begin(mode);}
API(capture) const u32* capture(){for(u32 group=0;group<2;++group){state[42+group*2]=state[43+group*2]=~0u;for(u32 i=0;i<6;++i){const u32 membership=current_mode==0?0:current_mode==2?1:i%2;auto* vm=manager.find(ids[i]);if(!vm||membership!=group)continue;if(!vm->registry.previous)state[42+group*2]=i;if(!vm->registry.next)state[43+group*2]=i;}}return state;}
