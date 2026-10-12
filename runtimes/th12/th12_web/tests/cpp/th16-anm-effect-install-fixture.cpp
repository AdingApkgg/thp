#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;alignas(4) static u8 heap[0x193c],code[24];
struct Environment:AnmEnvironment{u32 bytes=0;bool allocate_geometry(AnmVm& vm,u32 n)override{if(n>sizeof heap)return false;bytes=n;vm.geometry=heap;return true;}};
static Environment env;
API(run) i32 run(u32 flags,u32 flags2,u32 refs,i32 type){
 vm={};vm.initialize();env.rate=1;env.bytes=0;vm.timer.set(0,&env.rate);vm.th13_native_flags=flags;vm.flags2=flags2;vm.integers[0]=type;std::memset(heap,0xa5,sizeof heap);std::memset(code,0,sizeof code);
 auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(508);p->length=12;p->references=refs;const i32 arg=refs&1?10000:type;std::memcpy(code+8,&arg,4);
 auto* stop=reinterpret_cast<AnmInstruction*>(code+12);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(word) u32 word(u32 n){if(n==0x1934/4)return 0;u32 result=0;if(n<sizeof heap/4)std::memcpy(&result,heap+n*4,4);return result;}
API(selector) u32 selector(u32 n){return vm.th16_callbacks[n];}
API(size) u32 size(){return env.bytes;}
API(flags) u32 flags(){return vm.th13_native_flags;}
API(flags2) u32 flags2(){return vm.flags2;}
API(next_update) i32 next_update(){return vm.update(env);}
