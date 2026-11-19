#include "PlayerJizo.hpp"
namespace th143 {
namespace {
void reset(AnmView v,PlayerJizoHost& host){const u32 flags=v.get(0x14);if(!(flags&1)){v.put(0x10,host.global_rate_token());v.put(0x14,flags|1);}v.put(4,0xffffffff);v.put(8,0);v.put(12,0);}
bool tick(AnmView v,PlayerJizoHost& host){const u32 token=v.get(0x10),old=v.get(8);v.put(4,old);float rate=1;if(token&&!host.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=v.floating(12)+(unit?1.f:rate);v.put(12,word(value));v.put(8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool update_player_jizo(AnmView option,bool secondary,AnmView equipment,PlayerState* player,AnmView cheat,AnmWorld& world,PlayerJizoHost& host){
    if(!player)return true;auto& p=*player;auto ui=[&](i32 child,i32 signal){return signal_cheat_child(cheat,cheat.get(0x2b8),child,signal,world);};
    if(!option.get(0x1c)&&p.get(0x684)==4&&signed_word(option.get(0x18))>0){
        equipment.put(0x18,equipment.get(0x18)+1);
        if(!secondary&&equipment.get(0x1c)&&!host.jizo_alternate_release())return false;
        if(!ui(secondary?12:11,6)||!ui(secondary?8:7,6))return false;
        option.put(0x18,option.get(0x18)-1);option.put(0x1c,1);reset(option,host);
        p.put(0x1847c,p.get(0x1847c)|0x32);p.put(0x684,1);
        const std::array<float,3> position{p.floating(0x5e0),p.floating(0x5e4),p.floating(0x5e8)};
        u32 ignored;if(!world.create_at(p.get(0x10),22,-1,position,ignored)||!ui(secondary?12:11,59))return false;
    }
    if(option.get(0x1c)==1){
        if(option.get(8)==20)p.put(0x1847c,p.get(0x1847c)&~0x12u);
        if(signed_word(option.get(8))>=signed_word(option.get(0x2c))){
            for(u32 i=0;i<3;++i)option.put(0x3c+i*4,p.get(0x5e0+i*4));
            p.put(0x1847c,p.get(0x1847c)&~0x20u);option.put(0x1c,0);reset(option,host);
            if(!secondary&&signed_word(option.get(0x18))>0&&!ui(11,60))return false;
            if(!host.jizo_sound(77,p.floating(0x5e0)))return false;
            if(secondary&&signed_word(option.get(0x18))>0&&!ui(12,59))return false;
        }
    }return tick(option,host);
}
bool draw_player_jizo(AnmView option,bool secondary,PlayerState* player,AnmView ascii,PlayerJizoDrawState& scratch,PlayerJizoHost& host){
    if(!option.get(0x1c)||signed_word(option.get(8))>=40)return true;if(!player)return false;
    const auto& p=*player;std::array<float,3> position{p.floating(0x5e0)-20.f,p.floating(0x5e4)-40.f,p.floating(0x5e8)};
    if(secondary){scratch.flags|=1;position[0]+=320.f;position[1]+=16.f;for(u32 i=0;i<3;++i)scratch.position[i]=word(position[i]);}
    else ascii.put(0x191cc,1);
    ascii.put(0x191c8,2);const bool flash=signed_word(option.get(8))%8<4,remaining=option.get(0x18)!=0;
    ascii.put(0x191b0,remaining?(flash?0xffffffff:0xff808080):(flash?0xffff8080:0xffa00000));
    if(!host.jizo_remaining(position,signed_word(option.get(0x18))))return false;
    if(!secondary)ascii.put(0x191cc,0);ascii.put(0x191c8,0);ascii.put(0x191b0,0xffffffff);return true;
}
}
