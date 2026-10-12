#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;
static AnmEnvironment env;
static AnmResource file,fallback;
alignas(4) static u8 code[32];
static i32 callback(AnmVm&,i32 value){return value+1;}
API(run) i32 run(i32 value,u32 refs,u32 cb,i32 frame,u32 op,u32 bound,u32 seed){
    file={};fallback={};
    for(auto* r:{&file,&fallback}){r->textures.resize(1);r->textures[0].width=512;r->textures[0].height=256;r->sprites.resize(r==&file?4:259);}
    for(u32 i=0;i<4;++i){auto& s=file.sprites[i];s.width=31.5f+i;s.height=17.25f+i;s.u0=.125f;s.v0=.25f;s.u1=.75f;s.v1=.875f;}
    auto& s=fallback.sprites[258];s.width=s.height=1;s.u0=.125f;s.v0=.25f;s.u1=.75f;s.v1=.875f;
    vm={};vm.initialize();vm.flags=6;vm.resource=&file;vm.timer.set(frame,&env.rate);vm.integers[0]=value;
    vm.integers[1]=bound;env.script_rng={u16(seed),0,0};
    vm.sprite_callback=cb?callback:nullptr;env.fallback_sprites=&fallback;
    std::memset(code,0,sizeof(code));auto* command=reinterpret_cast<AnmInstruction*>(code);
    command->opcode=anm_canonical_opcode(op);command->length=op==300?12:16;command->references=refs;
    const i32 args[]={(refs&1)?10000:value,(refs&2)?10001:i32(bound)};std::memcpy(code+8,args,op==300?4:8);
    auto* next=reinterpret_cast<AnmInstruction*>(code+command->length);next->length=8;next->time=30000;
    vm.script_begin=vm.instruction=command;return vm.update(env);
}
API(word) i32 word(u32 i){switch(i){case 0:return vm.sprite_index;case 1:return vm.bound_sprite_resource()==&fallback;case 2:return vm.resource==&file;case 3:return vm.flags&1;default:return vm.sprite_frame;}}
API(real) float real(u32 i){if(i<2)return i?vm.sprite_size.y:vm.sprite_size.x;if(i<10){float v;std::memcpy(&v,reinterpret_cast<u8*>(vm.uv)+(i-2)*4,4);return v;}if(i<26)return vm.sprite_matrix.m[i-10];if(i<42)return vm.transform_matrix.m[i-26];return vm.uv_matrix.m[i-42];}
API(rng) u32 rng(u32 i){return i?env.script_rng.calls:env.script_rng.seed;}
