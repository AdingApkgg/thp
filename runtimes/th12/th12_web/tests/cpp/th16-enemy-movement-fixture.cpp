#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/AnmVm.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;
static EnemyEnvironment environment;
static EnemyGlobals globals(enemy,environment);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(initialize) void initialize(const u32* words,float rate){
    std::memset(&enemy,0,sizeof enemy);std::memcpy(&enemy.previous,words,52*4);enemy.flags=words[52];
    enemy.clamp_center={10,100};enemy.clamp_size={25,35};enemy.visual_size={16,24};environment.rate=rate;
}
API(command) i32 command(u32 op,const u32* args){
    alignas(4) u8 data[44]{};auto* cmd=reinterpret_cast<EclInstruction*>(data);cmd->opcode=u16(op);cmd->length=44;std::memcpy(data+16,args,(op==425||op==426||op==427)?28:24);
    EclContext context;context.instruction=cmd;return enemy_th16_movement_command(enemy,context,globals);
}
API(tick) i32 tick(){enemy.flags|=0x40000u;const auto result=enemy.update_movement(&environment.rate,{.125f,-.25f,.5f});return result?result:enemy_th16_visibility(enemy);}
API(value) u32 value(u32 n){if(n==52)return enemy.flags;u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&enemy.previous)+n*4,4);return v;}
static i32 direction_words[2];
API(direction_case) i32 direction_case(u32 flags,i32 direction,u32 velocity){enemy.flags=flags;enemy.direction=direction;enemy.current.velocity.x=float_bits(velocity);enemy.base_animation=0;return enemy_th16_direction_request(enemy,direction_words[0],direction_words[1]);}
API(direction_word) i32 direction_word(u32 n){return direction_words[n];}
static AnmVm mark_vms[5];
API(mark_case) void mark_case(u32 a,u32 b,u32 c,u32 d,u32 e){
    const u32 flags[]={a,b,c,d,e};for(u32 n=0;n<5;++n){mark_vms[n].initialize();mark_vms[n].flags2=flags[n];mark_vms[n].child.value=&mark_vms[n];}
    const u32 order[]={0,1,3,4,2};for(u32 n=0;n<4;++n)mark_vms[order[n]].child.next=&mark_vms[order[n+1]].child;
    mark_vms[1].parent=mark_vms[2].parent=&mark_vms[0];mark_vms[3].parent=mark_vms[4].parent=&mark_vms[1];enemy_th16_mark_animation(mark_vms[0]);
}
API(mark_word) u32 mark_word(u32 n){return mark_vms[n].flags2;}
API(interpolation_value) u32 interpolation_value(u32 index,u32 n){
    const auto& v=enemy.th16_motion_interpolation[index];
    const u32 words[]={float_bits(v.start[0]),float_bits(v.end[0]),float_bits(v.initial_tangent[0]),float_bits(v.final_tangent[0]),
        u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.rate?1u:0u,v.timer.flags,u32(v.duration),u32(v.mode)};
    return words[n];
}
API(position_value) u32 position_value(u32 index,u32 n){
    const auto& v=index?enemy.relative_position:enemy.absolute_position;
    if(n<12){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&v)+4*n,4);return word;}
    const u32 words[]={u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.rate?1u:0u,v.timer.flags,u32(v.duration),u32(v.mode)};
    return words[n-12];
}
