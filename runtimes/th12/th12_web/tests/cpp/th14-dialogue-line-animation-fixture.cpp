#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource text;static AnmVm* vm;static u32 state[16];
static u32 float_bits(float value){u32 bits;std::memcpy(&bits,&value,sizeof(bits));return bits;}
static void capture(){state[0]=u32(i32(vm->sprite_index));state[1]=vm->color;state[2]=vm->secondary_color;state[3]=vm->layer;state[4]=u32(vm->timer.current);state[5]=float_bits(vm->timer.fractional);state[6]=float_bits(vm->script_position.x);state[7]=float_bits(vm->script_position.y);state[8]=float_bits(vm->script_position.z);state[9]=float_bits(vm->scale.x);state[10]=float_bits(vm->scale.y);state[11]=u32(vm->pending_interrupt);state[12]=vm->rectangle_columns|(u32(vm->rectangle_rows)<<8);state[13]=vm->flags2&0xa00;state[14]=vm->flags&1;state[15]=vm->instruction?u32(reinterpret_cast<u8*>(vm->instruction)-reinterpret_cast<u8*>(vm->script_begin)):0xffffffff;}
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_text) i32 load_text(const u8* p,u32 n){return text.open(p,n)&&manager.prepare_resource(text,0);}
API(begin_line) i32 begin_line(i32 slot,float rate,i32 second){manager.clear();manager.rate=rate;vm=manager.create(text,slot,0,22);if(!vm)return 0;vm->rectangle_columns=vm->rectangle_rows=21;vm->flags2|=0x800;if(second)vm->interrupt(7);capture();return 1;}
API(step) i32 step(i32 label){if(label>=0)vm->interrupt(label);const auto result=vm->update(manager);capture();return result;}
API(data) const u32* data(){return state;}
