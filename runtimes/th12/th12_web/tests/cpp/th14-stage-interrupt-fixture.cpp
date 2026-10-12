#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/EnemyScript.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource resource;
static u32 background;
static Stage stage(manager,resource,resource,background,1);
static float other=.5f;
API(run) i32 run(u32 variant,i32 marker,u32 flags,u32 pointer,u32 ecl){
 stage.resource={};stage.state={};stage.state.instruction_offset=0x777;stage.state.script_timer={123,456,789.25f,pointer==0?nullptr:pointer==1?&other:&manager.rate,flags};
 i32 times[]={10,300,700,900,1100,1200,-1};if(variant==1)times[0]=-1;if(variant==2)times[3]=-1;if(variant==3)times[1]=16777217;
 const i16 ops[]={16,0,16,0,16,0,0};u32 offset=0;
 for(u32 n=0;n<7;++n){StageInstruction ins;ins.time=times[n];ins.opcode=ops[n];ins.length=ops[n]==16?12:8;ins.offset=offset;if(ops[n]==16)ins.arguments.push_back(n==0?7:2);offset+=u32(ins.length);stage.resource.instructions.push_back(ins);}
 if(!ecl)return stage.interrupt(marker)?0:-2;
 EnemyState enemy;EnemyEnvironment env;EnemyCommandEnvironment commands;commands.stage=&stage;EnemyScriptServices services(enemy,env,commands);
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=630;ins->length=20;std::memcpy(bytes+16,&marker,4);EclContext c;c.instruction=ins;return services.command(c);
}
API(word) u32 word(u32 n){const auto& t=stage.state.script_timer;switch(n){case 0:return stage.state.instruction_offset;case 1:return u32(t.previous);case 2:return u32(t.current);case 3:return float_bits(t.fractional);case 4:return t.flags;default:return !t.rate?0:t.rate==&other?1:2;}}
