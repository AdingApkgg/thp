#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/EnemyCallbacks.hpp"
#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/LaserManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState bullets[6];static EnemyState enemy;static EnemyEnvironment env;static EnemyCommandEnvironment commands;
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) void run(u32 count,u32 radius,u32 px,u32 py,const u32* input){
 for(u32 n=0;n<count;++n){auto& b=bullets[n];b={};b.position={float_bits(input[6*n]),float_bits(input[6*n+1]),float_bits(input[6*n+2])};b.extra=signed_bits(input[6*n+3]);b.transform_index=signed_bits(input[6*n+4]);b.active_transforms=input[6*n+5];b.th16_active_next=n+1<count?&bullets[n+1]:nullptr;}
 enemy_th16_nearby_bullets(count?bullets:nullptr,float_bits(radius),{float_bits(px),float_bits(py),0});
}
API(value) u32 value(u32 n){auto& b=bullets[n/3];return n%3==0?u32(b.extra):n%3==1?u32(b.transform_index):b.active_transforms;}
API(selector) i32 selector(i32 index,u32 mode){
 enemy={};enemy.callbacks[0]=17;enemy.callbacks[1]=signed_bits(mode);alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=632;cmd->length=20;std::memcpy(bytes+16,&index,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,env,commands);return services.command(c);
}
API(selector_word) u32 selector_word(u32 n){return n==0?u32(enemy.callbacks[0]):n==1?u32(enemy.callbacks[1]):u32(enemy.tick_callback==EnemyTick::Th16NearbyBullets);}
API(empty_reset) i32 empty_reset(){
 AnmResource resource;AnmManager anm;LaserWorld laser_world;LaserManager lasers(resource,anm,laser_world);EclProgram program;World world;EnemyManager manager(program,env,commands,world);commands.lasers=&lasers;
 alignas(4) u8 bytes[16]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=545;cmd->length=16;EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,env,commands);const i32 result=services.command(c);commands.lasers=nullptr;return result==0&&!lasers.active_count&&lasers.next_id==0x10000&&lasers.last_error==0?0:-2;
}
