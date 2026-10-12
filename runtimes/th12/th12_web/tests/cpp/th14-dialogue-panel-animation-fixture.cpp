#include "../../cpp/game/AnmManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front;static AnmVm* vm;static u32 state[20];
static u32 bits(float value){u32 result;std::memcpy(&result,&value,4);return result;}
static void capture(){
 state[0]=u32(i32(vm->sprite_index));state[1]=vm->color;state[2]=vm->secondary_color;state[3]=vm->layer;state[4]=u32(vm->timer.current);state[5]=bits(vm->timer.fractional);
 state[6]=bits(vm->script_position.x);state[7]=bits(vm->script_position.y);state[8]=bits(vm->script_position.z);state[9]=bits(vm->scale.x);state[10]=bits(vm->scale.y);state[11]=u32(vm->pending_interrupt);
 state[12]=bits(vm->floats[0]);state[13]=bits(vm->floats[1]);state[14]=bits(vm->texture_scale.x);state[15]=bits(vm->texture_scale.y);
 state[16]=vm->rectangle_columns|(u32(vm->rectangle_rows)<<8);state[17]=vm->flags2&0xa00;state[18]=vm->flags&1;state[19]=vm->instruction?u32(reinterpret_cast<u8*>(vm->instruction)-reinterpret_cast<u8*>(vm->script_begin)):0xffffffff;
}
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_front) i32 load_front(const u8* p,u32 n){return front.open(p,n)&&manager.prepare_resource(front,5);}
API(begin_panel) i32 begin_panel(i32 slot,float rate,float width){manager.clear();manager.rate=rate;vm=manager.create(front,slot,5,22);if(!vm)return 0;vm->floats[0]=width;capture();return 1;}
API(step) i32 step(i32 label){if(label>=0)vm->interrupt(label);const auto result=vm->update(manager);capture();return result;}
API(data) const u32* data(){return state;}
