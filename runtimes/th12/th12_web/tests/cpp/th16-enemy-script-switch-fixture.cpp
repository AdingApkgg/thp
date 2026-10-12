#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/EnemyScript.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy targets[2],caller;static EnemyLink nodes[2];static EnemyEnvironment environment;static EnemyCommandEnvironment commands;
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};
static World world;static EclProgram program;static EclResource resource;static EnemyManager manager(program,environment,commands,world);
alignas(4) static u8 instruction[32];static u32 selected;
API(run_case) i32 run_case(u32 count,i32 id,u32 threads,i32 dirty,u32 exists,i32 duration,u32 flags){
 for(auto& target:targets){EnemyScriptServices services(target.state,environment,commands);target.script.release_threads(services);target={};}
 caller={};caller.state.script_owner=&caller;manager.first=count?nodes:nullptr;
 resource.bytes.assign(48,0);resource.subroutines={{"Switch",0,48}};program.definitions=exists?std::vector<EclProgram::Definition>{{&resource,0}}:std::vector<EclProgram::Definition>{};
 for(u32 j=0;j<2;++j){
  auto& target=targets[j];target.state.instance_id=7+j*2;target.state.script_owner=&target;target.script.initialize_context();target.script.program=&program;
  auto& c=target.script.root;c.time=3.5f;c.instruction=reinterpret_cast<const EclInstruction*>(instruction);c.stack.top=c.stack.frame_base=dirty;c.thread_id=37;c.state=9;c.difficulty=0xa;c.flags=flags;
  const u32 local=0x12345678;std::memcpy(c.stack.data,&local,4);
  for(u32 k=0;k<8;++k){c.th16_scalars[k].value.duration=duration+i32(k);c.th16_scalars[k].current=float_bits(0x3f800000+k);}
  for(u32 k=0;k<threads;++k){auto* node=new EclThread{};node->value=new EclContext{};node->next=target.script.threads.next;node->previous=&target.script.threads;if(node->next)node->next->previous=node;target.script.threads.next=node;}
  nodes[j]={&target,j+1<count?&nodes[j+1]:nullptr,j?&nodes[j-1]:nullptr};
 }
 auto* ins=reinterpret_cast<EclInstruction*>(instruction);*ins={};ins->opcode=800;ins->length=32;std::memcpy(instruction+16,&id,4);std::memcpy(instruction+24,"Switch",7);
 EclContext c;c.instruction=ins;commands.manager=&manager;EnemyScriptServices services(caller.state,environment,commands);
 const auto result=services.command(c);selected=!count||!id?0xffffffff:id==7?0:count==2?1:0;return result;
}
API(value) u32 value(u32 n){
 if(!n)return selected;--n;auto& target=targets[n/27];auto& c=target.script.root;const u32 field=n%27;
 const u32 values[]={float_bits(c.time),u32(c.instruction!=nullptr),c.instruction==reinterpret_cast<const EclInstruction*>(instruction)?128u:0u,u32(c.stack.frame_base),u32(c.stack.top),u32(c.thread_id),c.state,c.difficulty,*reinterpret_cast<u32*>(c.stack.data)};
 if(field<9)return values[field];if(field<17)return u32(c.th16_scalars[field-9].value.duration);if(field<25)return float_bits(c.th16_scalars[field-17].current);
 return field==25?u32(target.script.threads.next!=nullptr):u32(target.script.active==&c);
}
