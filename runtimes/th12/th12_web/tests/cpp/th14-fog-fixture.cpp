#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/Stage.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource a,t;static u32 background;static Stage stage(manager,a,t,background,3);
static EnemyState e;static EnemyEnvironment environment;static EnemyGlobals globals(e,environment);static EnemyCommandEnvironment world;
API(run) i32 run(i32 duration,float rate,u32 color){
    stage.state={};environment.rate=rate;stage.state.camera.fog.set(0x668899aa,15,900);world.stage=&stage;
    alignas(4) u8 bytes[36]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=557;cmd->length=36;
    const u32 args[]={u32(duration),0,color,float_bits(-3.25f),float_bits(450.125f)};std::memcpy(bytes+16,args,20);EclContext c;c.instruction=cmd;
    return enemy_th14_state_command(e,c,globals,world);
}
API(tick) void tick(){auto& s=stage.state;if(s.fog_interpolation.duration)s.camera.fog=sample(s.fog_interpolation,&environment.rate);}
API(fog_value) u32 fog_value(u32 n){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&stage.state.camera.fog)+4*n,4);return word;}
API(band_value) u32 band_value(u32 n){const auto& v=stage.state.fog_interpolation;if(n<14){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&v)+4*n,4);return word;}
    const u32 words[]={u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.rate?1u:0u,v.timer.flags,u32(v.duration),u32(v.mode)};return words[n-14];}
