#include "../../cpp/game/PlayerMotion.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;static AnmResource file;struct World:PlayerMotionWorld{};static World world;static PlayerMotion motion(file,file,animations,world);static u32 handles[24];
API(begin) i32 begin(u32 base,i32 focus,i32 recall,i32 clock,i32 lerp,u32 seed,i32 snap,i32 present){
 animations.clear();file.scripts.resize(1);auto& bytes=file.scripts[0].bytes;bytes.resize(16);const AnmInstruction idle{i16(anm_canonical_opcode(2)),8,0,0},end{-1,8,0,0};std::memcpy(bytes.data(),&idle,8);std::memcpy(bytes.data()+8,&end,8);
 motion.options={};motion.state={};const i32 x[]={-321,2147480000,-2147480000},y[]={50319,-2147480000,2147480000};motion.state.x=x[seed];motion.state.y=y[seed];motion.state.focused=focus;motion.state.flags=recall*2;motion.state.option_lerp=lerp;motion.state.recall_timer=clock;
 const u32 offsets[]={0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4};
 for(u32 i=0;i<12;++i){auto& o=motion.options[i];for(auto k:offsets){const u32 v=17+i*31+k+seed*100000003;std::memcpy(reinterpret_cast<u8*>(&o)+k,&v,4);}o.state=i%3==seed?0:2;o.snap=snap;
  for(u32 aux=0;aux<2;++aux){auto* vm=animations.create(file,0,9,14);if(!vm)return -1;vm->position={91,-72,33};vm->pending_interrupt=77;handles[i*2+aux]=vm->id;if(aux)o.auxiliary=present?vm->id:0;else o.animation=present?vm->id:0;}}
 return motion.update_options_th16(base,base==0?4:8)?1:motion.last_error;
}
API(option) u32 option(u32 i,u32 k){const u32 offsets[]={0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4};u32 v;std::memcpy(&v,reinterpret_cast<u8*>(&motion.options[i])+offsets[k],4);return v;}
API(animation) u32 animation(u32 n,u32 k){const auto* vm=animations.find(handles[n]);return k==0?float_bits(vm->position.x):k==1?float_bits(vm->position.y):k==2?float_bits(vm->position.z):u32(vm->pending_interrupt);}
