#include "EnemyContact.hpp"
#include <cmath>
namespace th143 {
namespace {
u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}
void set_timer(ActorState& s,u32 at,u32 value,u32 rate){
    if(!(s.get(at+16)&1)){s.put(at+12,rate);s.put(at+16,s.get(at+16)|1);}
    s.put(at,value-1);s.put(at+4,value);s.put(at+8,word(float(signed_word(value))));
}
void reset_phase(ActorState& s,u32 rate){set_timer(s,0x35c,0,rate);}
void tint(AnmView vm,u32 color){vm.put(0x18,(vm.get(0x18)&~0x40000u)|0x20000);vm.put(0x538,color);}
float wrap(float angle){u32 count=0;while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}return angle;}
}
bool contact_enemy(ActorState& s,EnemyContactGlobals& g,EnemyContactHost& host,i32& result){
    result=0;u32 flags=s.get(0x4100);
    if(flags&0x10000000){
        if(g.cheat_mode==1&&!(flags&0x20000000)){
            s.put(0x310,s.get(0x4108));auto vm=host.enemy_visual(s.get(0x124));if(vm.data&&!host.enemy_visual_script(vm,signed_word(s.get(0x310))))return false;
            s.put(0x4100,s.get(0x4100)|0x20000001);
        }else if(g.cheat_mode!=1&&(flags&0x20000000)){
            s.put(0x310,s.get(0x410c));auto vm=host.enemy_visual(s.get(0x124));if(vm.data&&!host.enemy_visual_script(vm,signed_word(s.get(0x310))))return false;
            s.put(0x4100,s.get(0x4100)&~0x20000001u);
        }
    }
    s.put(0x4100,s.get(0x4100)&~0x200000u);
    if(!(s.get(0x4100)&0x21)){
        u32 incoming=0,hit_flag=0;
        if(s.fields.floating(0x110)>0.f){
            PlayerShotImpactQuery q;for(u32 i=0;i<3;++i)q.position[i]=s.fields.floating(0x44+i*4);q.rectangle=(s.get(0x4100)&0x1000)!=0;q.owner=s.get(0x41b8);q.id=s.id;
            q.size={s.fields.floating(0x110),s.fields.floating(0x114)};q.angle=q.rectangle?s.fields.floating(0x120):0;q.radius=q.rectangle?0:s.fields.floating(0x110)*.5f;
            PlayerShotContactResult out;out.last_position={s.fields.floating(0x320),s.fields.floating(0x324),s.fields.floating(0x328)};
            if(!host.incoming_shots(q,out))return false;incoming=u32(out.damage);hit_flag=out.hit_flag;
            for(u32 i=0;i<3;++i)s.put(0x320+i*4,word(out.last_position[i]));
        }
        if(const u32 callback=s.get(0x41e0)){i32 additional;if(!host.damage_callback(callback,s,signed_word(incoming),additional))return false;incoming+=u32(additional);}
        if(signed_word(s.get(0x407c))>0){incoming+=s.get(0x407c);s.put(0x407c,0);}
        if(g.player_state==0||g.player_state==2)incoming=u32(signed_word(incoming)/5);
        if(g.hud_blocked)incoming=0;
        else if(signed_word(incoming)>0){
            if(hit_flag){u32 counted=incoming;if(signed_word(incoming)>=signed_word(s.get(0x4018)))counted=u32(signed_word(incoming-s.get(0x4018))/4)+s.get(0x4018);g.bomb_damage+=counted;}
            else g.normal_damage+=incoming;
        }
        if(g.cheat_mode==1&&1.f>s.fields.floating(0x40e0)){
            const float factor=s.fields.floating(0x40e0);if(incoming&&!(0.f<factor)&&!host.enemy_sound(36,s.fields.floating(0x44)))return false;
            incoming=truncate(float(signed_word(incoming))*factor);
        }
        if(incoming){
            if((g.phase.special_flags&0x21)==0x21)incoming=u32(signed_word(incoming)/30);
            if((s.get(0x4100)&0x10)||signed_word(s.get(0x409c))>0)s.put(0x402c,s.get(0x402c)+incoming);
            else damage_enemy_health(s,signed_word(incoming));
            set_timer(s,0x40cc,30,host.global_rate_token());
            const u32 script=advance_enemy_phase(s,g.phase,host.global_rate_token());
            if(script){reset_phase(s,host.global_rate_token());i32 code;if(!host.phase_script(s,script,true,code))return false;if(code){result=-1;return true;}}
            if(signed_word(s.get(0x4018))<=0&&!(s.get(0x4100)&0x80)){i32 code;if(!host.enemy_death(s,code))return false;if(code){result=1;return true;}}
            s.put(0x4100,s.get(0x4100)|0x200000);
        }
    }
    if(s.get(0x4030)&2){i32 code;if(!host.enemy_death(s,code))return false;if(code){result=1;return true;}}
    if(const u32 script=advance_enemy_phase(s,g.phase,host.global_rate_token())){reset_phase(s,host.global_rate_token());i32 ignored;if(!host.phase_script(s,script,false,ignored))return false;}
    if(!(s.get(0x4100)&0x22)&&signed_word(s.get(0x40b0))<=0&&!(s.get(0x4100)&0x4000000)){
        if(const u32 callback=s.get(0x41e4)){if(!host.body_callback(callback,s))return false;}
        else{
            i32 body=0;if(s.get(0x4100)&0x1000){
                auto vm=host.enemy_visual(s.get(0x124));if(!vm.data){s.put(0x124,0);return false;}
                const float angle=wrap(vm.floating(0x50)+real(0x3fc90fdb)),sn=float(std::sin(double(angle))),cs=float(std::cos(double(angle))),half=s.fields.floating(0x11c)*.5f;
                const std::array<float,3> position{s.fields.floating(0x44)+(cs*0.f-sn*half),s.fields.floating(0x48)+(cs*half+sn*0.f),s.fields.floating(0x4c)+0.f};
                if(!host.body_rectangle(position,s.fields.floating(0x118),s.fields.floating(0x11c),s.fields.floating(0x120),body))return false;
            }
            else if(!host.body_circle({s.fields.floating(0x44),s.fields.floating(0x48),s.fields.floating(0x4c)},s.fields.floating(0x118)*.5f,body))return false;
            if((s.get(0x4100)&0x200)&&body==2&&signed_word(s.get(0x360))%6==0&&!host.body_graze())return false;
        }
    }
    auto vm=host.enemy_visual(s.get(0x124));
    if(!vm.data)s.put(0x124,0);
    else if(s.get(0x408c)){vm.put(0x18,vm.get(0x18)&~0x60000u);s.put(0x408c,s.get(0x408c)-1);}
    else{
        const bool fourth=signed_word(s.get(0x360))%4==0;
        if(s.get(0x4100)&0x80000000){if(fourth)tint(vm,0xffff00ff);else vm.put(0x18,vm.get(0x18)&~0x60000u);}
        const bool special=(g.phase.special_flags&1)!=0;
        const bool ordinary_or_visible=!special||!(g.phase.special_flags&8);
        if(s.get(0x4100)&0x200000){
            tint(vm,0xff0000ff);s.put(0x408c,4);i32 sound=signed_word(s.get(0x4094));
            if(sound<0){const bool low=(s.get(0x4100)&0x40800000)&&ordinary_or_visible&&signed_word(s.get(0x4020))<(special?200:900);sound=low?35:34;}
            if(!host.enemy_sound(sound,s.fields.floating(0x44)))return false;
        }else if(!fourth)vm.put(0x18,vm.get(0x18)&~0x60000u);
        else if((s.get(0x4100)&0x40800000)&&ordinary_or_visible&&signed_word(s.get(0x4020))<(special?100:500))tint(vm,0xff0000ff);
    }
    if(signed_word(s.get(0x40d0))>0){
        s.put(0x40cc,s.get(0x40d0));float rate=1;const u32 token=s.get(0x40d8);if(token&&!host.timer_rate(token,rate))return false;
        const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=s.fields.floating(0x40d4)-(unit?1.f:rate);
        s.put(0x40d4,word(value));s.put(0x40d0,truncate(value));
    }
    return true;
}
}
