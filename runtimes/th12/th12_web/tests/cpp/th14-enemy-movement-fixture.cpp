#include "../../cpp/game/EnemyCommands.hpp"
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
    alignas(4) u8 data[44]{};auto* cmd=reinterpret_cast<EclInstruction*>(data);cmd->opcode=u16(op);cmd->length=44;std::memcpy(data+16,args,(op==421||op==423||op==425||op==426||op==427)?28:24);
    EclContext context;context.instruction=cmd;return enemy_th14_movement_command(enemy,context,globals);
}
API(state_command) i32 state_command(u32 op,const u32* args,u32 count){
    alignas(4) u8 data[64]{};auto* cmd=reinterpret_cast<EclInstruction*>(data);cmd->opcode=u16(op);
    cmd->length=u16(16+4*count);std::memcpy(data+16,args,count*4);
    EclContext context;context.instruction=cmd;static EnemyCommandEnvironment world;return enemy_th14_state_command(enemy,context,globals,world);
}
// The slot's own offsets are the emitter record's +8: the record at native +0x598 holds the
// sprite and the colour first, and the fields 700/701 address are at +0x5a0 and up.
API(slot_value) u32 slot_value(u32 slot,u32 field){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&enemy.th14_emitters[slot])+8+field,4);return v;}
API(record_word) u32 record_word(u32 index,u32 n){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&enemy.th14_emitters[index])+4*n,4);return v;}
API(fire_head) void fire_head(u32 index){enemy_th14_fire_position(enemy,index);}
// The case-702 check has to put the machine's slot record and the two per-index triples into the
// port before running the command, and read 0x2be's request back out of the entity.
API(offset_of) u32 offset_of(u32 which){
    switch(which){case 0:return u32(offsetof(EnemyState,th14_emitters));case 1:return u32(offsetof(EnemyState,th14_request));
    case 2:return u32(offsetof(EnemyState,th14_base_vectors));case 3:return u32(offsetof(EnemyState,th14_offset_vectors));}
    return 0;
}
API(seed) void seed(u32 offset,const u32* words,u32 count){std::memcpy(reinterpret_cast<u8*>(&enemy)+offset,words,count*4);}
API(request_word) u32 request_word(u32 n){u32 v;std::memcpy(&v,enemy.th14_request.bytes+4*n,4);return v;}
API(tick) i32 tick(){enemy.flags&=~0x40000u;const auto result=enemy.update_movement(&environment.rate,{.125f,-.25f,.5f});return result?result:enemy_th14_visibility(enemy);}
API(value) u32 value(u32 n){if(n==52)return enemy.flags;u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&enemy.previous)+n*4,4);return v;}
API(interpolation_value) u32 interpolation_value(u32 index,u32 n){
    const auto& v=enemy.motion_interpolation[index];
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
API(random_setup) void random_setup(u32 seed,float x){environment.random={u16(seed),0,0};environment.shared_random=nullptr;environment.player_position.x=x;}
API(random_value) u32 random_value(u32 n){return n?environment.random.calls:environment.random.seed;}
