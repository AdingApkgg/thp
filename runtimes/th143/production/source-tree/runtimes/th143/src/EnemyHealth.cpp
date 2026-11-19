#include "EnemyHealth.hpp"
namespace th143 {
namespace {
void reset_phase_timer(ActorState& s,u32 rate){
    if(!(s.get(0x36c)&1)){s.put(0x368,rate);s.put(0x36c,s.get(0x36c)|1);}
    s.put(0x35c,0xffffffff);s.put(0x360,0);s.put(0x364,0);
}
}
void damage_enemy_health(ActorState& s,i32 damage){
    const u32 value=u32(damage);s.put(0x402c,s.get(0x402c)+value);
    if(s.get(0x4030)&1){s.put(0x4024,s.get(0x4024)-value);const i32 remainder=signed_word(s.get(0x4024)-s.get(0x4028)*7);s.put(0x4018,u32(remainder/7)+s.get(0x4028));}
    else s.put(0x4018,s.get(0x4018)-value);
}
u32 advance_enemy_phase(ActorState& s,EnemyPhaseGlobals& g,u32 rate){
    const i32 health=signed_word(s.get(0x4018));s.put(0x4020,u32(health));s.put(0x4028,0);
    for(u32 i=0;i<8;++i){const u32 at=0x4118+i*20;const i32 threshold=signed_word(s.get(at));if(threshold<0)continue;
        s.put(0x4020,u32(health)-u32(threshold));s.put(0x4028,u32(threshold));
        if(health<=threshold){s.put(0x4018,u32(threshold));s.put(at,0xffffffff);if(!s.get(at+16))reset_phase_timer(s,rate);s.put(0x4100,s.get(0x4100)&~0x1000000u);return s.get(at+8);}break;
    }
    for(u32 i=0;i<8;++i){const u32 at=0x4118+i*20;const i32 threshold=signed_word(s.get(at)),timeout=signed_word(s.get(at+4));if(threshold<0||timeout<=0)continue;
        if(s.get(0x4100)&0x800000){const i32 remaining=signed_word(u32(timeout)-s.get(0x360));i32 seconds=remaining/60,hundredths=(remaining%60)*100/60;if(seconds>99)seconds=hundredths=99;g.countdown_seconds=seconds;g.countdown_hundredths=hundredths;}
        if(signed_word(s.get(0x360))<timeout)return 0;
        s.put(0x4018,u32(threshold));s.put(at,0xffffffff);reset_phase_timer(s,rate);s.put(0x4100,s.get(0x4100)|0x1000000);
        if(!(g.special_flags&8)){g.special_flags|=0x80;g.manager_phase=0;}return s.get(at+12);
    }
    return 0;
}
}
