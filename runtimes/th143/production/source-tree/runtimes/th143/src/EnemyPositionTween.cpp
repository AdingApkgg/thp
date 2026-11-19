#include "EnemyPositionTween.hpp"
namespace th143 {
bool start_enemy_position_tween(ActorState& actor,bool relative,i32 duration,i32 mode,float x,float y,AnmTimerHost& host){
    const u32 base=relative?0xcc:0x88,at=relative?0x404:0x39c;AnmView state{actor.fields.data.data()+at};
    if(duration<=0){state.put(0x50,0);return true;}
    state.put(0x50,u32(duration));for(u32 i=0;i<3;++i){state.put(0x24+i*4,0);state.put(0x30+i*4,0);state.put(0x0c+i*4,actor.get(base+i*4));}
    state.put(0x60,u32(mode));state.put(0x64,state.get(0x64)&~1u);
    state.put(0x18,double(x)>-999999.?word(x):actor.get(base));state.put(0x1c,double(y)>-999999.?word(y):actor.get(base+4));state.put(0x20,0);
    if(!(state.get(0x4c)&1)){state.put(0x48,host.global_rate_token());state.put(0x4c,state.get(0x4c)|1);}
    state.put(0x3c,0xffffffff);state.put(0x40,0);state.put(0x44,0);actor.put(base+0x40,actor.get(base+0x40)&~15u);return true;
}
bool sample_enemy_position_tween(AnmView state,AnmTimerHost& host,std::array<u32,3>& value){
    if(state.get(0x64)&1)return false;
    // The arithmetic is the verified float3 evaluator. Only its typed field
    // layout differs: enemy current/from/target/tangents precede the timer.
    std::array<u8,0x58> bytes{};AnmView mapped{bytes.data()};
    for(u32 i=0;i<3;++i){mapped.put(i*4,state.get(0x0c+i*4));mapped.put(0x0c+i*4,state.get(0x18+i*4));mapped.put(0x18+i*4,state.get(0x24+i*4));mapped.put(0x24+i*4,state.get(0x30+i*4));mapped.put(0x30+i*4,state.get(i*4));}
    std::memcpy(mapped.data+0x3c,state.data+0x3c,0x18);mapped.put(0x54,state.get(0x60));
    if(!anm_interpolate_vec3(mapped,host,false,value))return false;
    for(u32 i=0;i<3;++i){state.put(i*4,mapped.get(0x30+i*4));state.put(0x0c+i*4,mapped.get(i*4));state.put(0x18+i*4,mapped.get(0x0c+i*4));state.put(0x24+i*4,mapped.get(0x18+i*4));state.put(0x30+i*4,mapped.get(0x24+i*4));}
    std::memcpy(state.data+0x3c,mapped.data+0x3c,0x18);return true;
}
}
