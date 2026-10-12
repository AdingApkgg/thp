#include "../../cpp/game/EnemyManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static u32 words[24];
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};
API(run) i32 run(u32 selected,i32 caller_slot,u32 pattern,u32 mode,u32 threads,u32 refs){
 EnemyEnvironment env;EnemyCommandEnvironment commands;World world;EclResource resource;EclProgram program;
 resource.bytes.resize(48);resource.subroutines={{"Next",0,32}};program.definitions={{&resource,0}};
 const auto* next=program.find("Next");EnemyManager manager(program,env,commands,world);Enemy caller;Enemy targets[3];caller.state.boss_slot=caller_slot;
 for(u32 slot=0;slot<3;++slot){auto& target=targets[slot];target.state.script_owner=&target;target.script.initialize_context();target.script.program=&program;
  auto& c=target.script.root;c.time=float_bits(0x42f70000u+slot);c.instruction=reinterpret_cast<const EclInstruction*>(reinterpret_cast<const u8*>(next)+16);c.stack.top=128;c.stack.frame_base=64;c.flags=3;c.state=77;
  target.state.interrupts[selected]={mode&1?-1:177,99,mode&2?nullptr:"Next","Other"};commands.bosses[slot]=pattern&(1u<<slot)?&target.state:nullptr;
  for(u32 n=0;n<threads;++n){auto* node=static_cast<EclThread*>(std::calloc(1,sizeof(EclThread)));node->value=static_cast<EclContext*>(std::calloc(1,sizeof(EclContext)));node->next=target.script.threads.next;node->previous=&target.script.threads;if(node->next)node->next->previous=node;target.script.threads.next=node;}
 }
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=802;ins->length=20;ins->references=u16(refs);const u32 arg=refs?0:selected;std::memcpy(bytes+16,&arg,4);
 EclContext context;context.instruction=ins;std::memcpy(context.stack.data,&selected,4);EnemyScriptServices services(caller.state,env,commands);const i32 result=services.command(context);
 for(u32 slot=0;slot<3;++slot){auto& target=targets[slot];auto& c=target.script.root;const u32 state[]={float_bits(c.time),u32(c.instruction==next),u32(c.stack.top),u32(c.stack.frame_base),c.flags,c.state,u32(!!target.script.threads.next),u32(target.state.interrupts[selected].health)};std::memcpy(words+slot*8,state,sizeof(state));EnemyScriptServices cleanup(target.state,env,commands);target.script.release_threads(cleanup);}
 return result;
}
API(word) u32 word(u32 n){return n<24?words[n]:0xffffffff;}
