#include "../../cpp/game/EnemyAnimations.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static EnemyAnimations families(manager);static AnmResource front;static AnmVm* vms[4];static u32 state[88],statuses[4],linked[3];static bool alive[4],synchronous;
static u32 bits(float value){u32 result;std::memcpy(&result,&value,4);return result;}
static void capture(){for(u32 i=0;i<4;++i){const auto* vm=vms[i];auto* s=state+i*22;
 s[0]=u32(i32(vm->sprite_index));s[1]=vm->color;s[2]=vm->secondary_color;s[3]=vm->layer;s[4]=u32(vm->timer.current);s[5]=bits(vm->timer.fractional);
 s[6]=bits(vm->script_position.x);s[7]=bits(vm->script_position.y);s[8]=bits(vm->script_position.z);s[9]=bits(vm->scale.x);s[10]=bits(vm->scale.y);s[11]=u32(vm->pending_interrupt);
 s[12]=bits(vm->floats[0]);s[13]=bits(vm->floats[1]);s[14]=bits(vm->texture_scale.x);s[15]=bits(vm->texture_scale.y);
 s[16]=vm->rectangle_columns|(u32(vm->rectangle_rows)<<8);s[17]=vm->flags2&0xa00;s[18]=vm->flags&1;s[19]=vm->instruction?u32(reinterpret_cast<const u8*>(vm->instruction)-reinterpret_cast<const u8*>(vm->script_begin)):0xffffffff;s[20]=vm->parent==vms[0];s[21]=u32(i32(vm->script_index));
}}
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_front) i32 load_front(const u8* p,u32 n){return front.open(p,n)&&manager.prepare_resource(front,5);}
API(begin_family) i32 begin_family(i32 slot,float rate,float width,i32 immediate){manager.clear();manager.rate=rate;synchronous=immediate;vms[0]=manager.create(front,slot,5,22);if(!vms[0])return 0;u32 count=0;for(auto* node=vms[0]->child.next;node;node=node->next){auto* vm=node->value;linked[count++]=u32(i32(vm->script_index));const auto index=(i32(vm->script_index)-(slot-48))/16+1;if(index<1||index>3)return 0;vms[index]=vm;}if(count!=3)return 0;for(u32 i=0;i<4;++i)alive[i]=true;vms[1]->floats[0]=vms[3]->floats[0]=width;capture();return 1;}
API(interrupt_family) void interrupt_family(i32 label){if(synchronous)families.interrupt_now(vms[0]->id,label);else families.interrupt(vms[0]->id,i16(label));capture();}
API(step) void step(){for(u32 i=0;i<4;++i){const u32 index=(i+1)%4;statuses[i]=alive[index]?vms[index]->update(manager):1;alive[index]=!statuses[i];}capture();}
API(data) const u32* data(){return state;}
API(status) const u32* status(){return statuses;}
API(chain) const u32* chain(){return linked;}
