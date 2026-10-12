#include "../../cpp/game/EnemyAnimations.hpp"
#include <algorithm>
#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static EnemyAnimations families(manager);static AnmResource resource;static std::vector<AnmVm*> vms;static u32 state[16*22],statuses[16],linked[15],links;static bool alive[16],synchronous;
static u32 bits(float value){u32 result;std::memcpy(&result,&value,4);return result;}
static void capture(){for(u32 i=0;i<vms.size();++i){const auto* vm=vms[i];auto* s=state+i*22;
 s[0]=u32(i32(vm->sprite_index));s[1]=vm->color;s[2]=vm->secondary_color;s[3]=vm->layer;s[4]=u32(vm->timer.current);s[5]=bits(vm->timer.fractional);
 s[6]=bits(vm->script_position.x);s[7]=bits(vm->script_position.y);s[8]=bits(vm->script_position.z);s[9]=bits(vm->scale.x);s[10]=bits(vm->scale.y);s[11]=u32(vm->pending_interrupt);
 s[12]=bits(vm->floats[0]);s[13]=bits(vm->floats[1]);s[14]=bits(vm->texture_scale.x);s[15]=bits(vm->texture_scale.y);
 s[16]=vm->rectangle_columns|(u32(vm->rectangle_rows)<<8);s[17]=vm->flags2&0xa00;s[18]=vm->flags&1;s[19]=vm->instruction?u32(reinterpret_cast<const u8*>(vm->instruction)-reinterpret_cast<const u8*>(vm->script_begin)):0xffffffff;s[20]=vm->parent==vms[0];s[21]=u32(i32(vm->script_index));}}
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_resource) i32 load_resource(const u8* p,u32 n){manager.clear();return resource.open(p,n);}
API(begin_family) i32 begin_family(i32 slot,float rate,i32 immediate){manager.clear();manager.rate=rate;resource.templates.reset();if(!manager.prepare_resource(resource,5))return 0;synchronous=immediate;vms.clear();auto* root=manager.create(resource,slot,5,u32(-1));if(!root)return 0;vms.push_back(root);links=0;
 for(auto* node=root->child.next;node;node=node->next){linked[links++]=u32(i32(node->value->script_index));vms.push_back(node->value);}
 std::reverse(vms.begin()+1,vms.end());for(u32 i=0;i<vms.size();++i)alive[i]=true;capture();return 1;}
API(interrupt_family) void interrupt_family(i32 label){if(synchronous)families.interrupt_now(vms[0]->id,label);else families.interrupt(vms[0]->id,i16(label));capture();}
API(step) void step(){for(u32 i=0;i<vms.size();++i){const u32 index=(i+1)%vms.size();statuses[i]=alive[index]?vms[index]->update(manager):1;alive[index]=!statuses[i];}capture();}
API(data) const u32* data(){return state;}
API(status) const u32* status(){return statuses;}
API(chain) const u32* chain(){return linked;}
API(count) u32 count(){return vms.size();}

static AnmResource text_resource;static std::unique_ptr<Dialogue> dialogue;static std::vector<u8> message;
struct Effects:DialogueEffects{bool dialogue_sound(i32)override{return true;}};static Effects effects;
API(begin_dialogue_family) i32 begin_dialogue_family(u32 index,float rate,i32 immediate){
 if(dialogue)dialogue->clear();dialogue.reset();manager.clear();manager.rate=rate;resource.templates.reset();if(!manager.prepare_resource(resource,5))return 0;synchronous=immediate;
 const i32 routes[21][4]={{1,0,1,0},{1,1,1,0},{1,2,1,0},{1,0,2,0},{1,0,20,0},{2,0,2,0},{2,0,20,0},{3,0,2,0},{3,0,20,0},{4,0,2,0},{4,0,20,0},{4,0,2,1},{4,0,20,1},{5,0,2,0},{5,0,20,0},{6,0,2,0},{6,0,20,0},{7,0,2,0},{7,0,20,0},{7,0,2,1},{7,0,2,2}};if(index>=21)return 0;const auto* route=routes[index];
 text_resource={};text_resource.scripts.resize(2);const AnmInstruction stop[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};for(auto& script:text_resource.scripts){script.bytes.resize(sizeof stop);std::memcpy(script.bytes.data(),stop,sizeof stop);}if(!manager.prepare_resource(text_resource,0))return 0;
 message.resize(12);const u32 header[]={1,12,0};std::memcpy(message.data(),header,12);message.push_back(0);message.push_back(0);message.push_back(u8(route[2]));message.push_back(route[2]==1?0:4);if(route[2]!=1){const u32 selection=route[3];const auto* p=reinterpret_cast<const u8*>(&selection);message.insert(message.end(),p,p+4);}const u8 wait[]={0,0,11,4,0x58,2,0,0,0,0,0,0};message.insert(message.end(),wait,wait+sizeof wait);
 i32 file,script;if(route[2]!=1){if(!Dialogue::th14_asset(route[0],route[3],route[2],file,script))return 0;families.resources[file]={&resource,5};}
 dialogue=std::make_unique<Dialogue>(manager,text_resource,resource,text_resource,resource,text_resource,effects);dialogue->stage=route[0];dialogue->character=route[1];dialogue->th14_animations=&families;if(!dialogue->begin(message,0)||dialogue->update(0,0)!=0)return 0;
 const auto handle=route[2]==1?dialogue->state.animations[0]:route[2]==20?dialogue->state.animations[7]:dialogue->th14_enemy_portraits[route[3]];auto* root=manager.find(handle);if(!root)return 0;
 vms.clear();vms.push_back(root);links=0;for(auto* node=root->child.next;node;node=node->next){linked[links++]=u32(i32(node->value->script_index));vms.push_back(node->value);}std::reverse(vms.begin()+1,vms.end());for(u32 i=0;i<vms.size();++i)alive[i]=true;capture();return 1;
}
